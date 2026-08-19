import asyncio
import logging
import httpx
try:
    from telegram import Update  # type: ignore
    from telegram.ext import (  # type: ignore
        ApplicationBuilder,
        ContextTypes,
        CommandHandler,
        MessageHandler,
        filters,
    )
    telegram_available = True
except ImportError:
    class Update: pass
    class ContextTypes:
        DEFAULT_TYPE = object
    ApplicationBuilder = None
    CommandHandler = None
    MessageHandler = None
    filters = None
    telegram_available = False
from src.api.config import settings
from .agent import OpenClawAgent
from .dispatcher import base_dispatcher_service
import uvicorn
from typing import Optional
from fastapi import FastAPI, BackgroundTasks, Request, Response
from pydantic import BaseModel
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger("OpenClaw")

app = FastAPI()
agent = OpenClawAgent()


from src.api.utils.resilience import CircuitBreaker


class BotManager:
    def __init__(self):
        self.apps: dict[str, any] = {}
        self._starting_ids: set[str] = set()
        self.api_circuit_breaker = CircuitBreaker()
        self.http_client: httpx.AsyncClient | None = None
        self._background_tasks: set[asyncio.Task] = set()

    def run_background_task(self, coro):
        """Create a task and keep a strong reference to prevent garbage collection."""
        task = asyncio.create_task(coro)
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        return task

    @property
    def http(self) -> httpx.AsyncClient:
        if not self.http_client:
            self.http_client = httpx.AsyncClient(timeout=10.0, follow_redirects=True)
        return self.http_client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=True,
    )
    async def _fetch_users_with_bots(self) -> list[dict]:
        """Fetch users with async HTTP client and circuit breaking"""
        if self.api_circuit_breaker.is_open():
            logger.warning("API circuit breaker is OPEN - skipping user fetch")
            return []

        try:
            headers = {}
            if settings.INTERNAL_API_TOKEN:
                headers["Authorization"] = f"Bearer {settings.INTERNAL_API_TOKEN}"

            response = await self.http.get(
                f"{settings.API_URL}/api/v1/auth/internal/users-with-bots",
                headers=headers,
                timeout=5.0,
            )

            if response.status_code == 200:
                self.api_circuit_breaker.record_success()
                return response.json()

            self.api_circuit_breaker.record_failure()
            logger.error(f"Failed to fetch users: {response.status_code}")
            return None

        except Exception as e:
            self.api_circuit_breaker.record_failure()
            logger.exception(f"Error fetching users: {e}")
            raise

    async def start_bot(self, user_id: str, token: str):
        if not telegram_available:
            logger.warning(f"python-telegram-bot is not installed. Cannot start bot for user {user_id}.")
            return

        if user_id in self._starting_ids:
            logger.warning(f"Bot for user {user_id} is already starting. Skipping.")
            return

        if user_id in self.apps:
            await self.stop_bot(user_id)

        self._starting_ids.add(user_id)
        try:
            logger.info(f"Starting bot for user {user_id}...")
            application = ApplicationBuilder().token(token).build()

            # Use specific user_id in context for the agent
            async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="🦅 OpenClaw Online. Your private agent is ready.",
                )

            async def msg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
                tg_user_id = update.effective_user.id
                text = update.message.text

                response = await agent.process_message(tg_user_id, text)

                await context.bot.send_message(
                    chat_id=update.effective_chat.id, text=response
                )

            application.add_handler(CommandHandler("start", start_cmd))
            application.add_handler(
                MessageHandler(filters.TEXT & (~filters.COMMAND), msg_handler)
            )

            await application.initialize()
            await application.start()
            await application.updater.start_polling()

            self.apps[user_id] = application
            logger.info(f"Bot for user {user_id} started successfully.")
        except Exception as e:
            logger.exception(f"Failed to start bot for user {user_id}: {e}")
        finally:
            if user_id in self._starting_ids:
                self._starting_ids.remove(user_id)

    async def stop_bot(self, user_id: str):
        if user_id in self.apps:
            logger.info(f"Stopping bot for user {user_id}...")
            app = self.apps[user_id]
            try:
                await app.updater.stop()
                await app.stop()
                await app.shutdown()
            except Exception as e:
                logger.exception(f"Error during stop_bot: {e}")
            finally:
                del self.apps[user_id]

    def _init_master_bot(self):
        """Start the Master Bot from settings if configured."""
        if not (settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_ADMIN_ID):
            return
        if "0" in self.apps or "0" in self._starting_ids:
            return
        logger.info("Initializing Master Bot from system settings...")
        self.run_background_task(self.start_bot("0", settings.TELEGRAM_BOT_TOKEN))

    def _start_user_bots(self, users: list[dict]):
        """Auto-start bots for fetched users."""
        logger.info(f"Auto-starting bots for {len(users)} users...")
        for user in users:
            user_id = user.get("id")
            token = user.get("telegram_token")
            if not (user_id and token):
                continue
            user_id_str = str(user_id)
            if user_id_str in self.apps or user_id_str in self._starting_ids:
                continue
            self.run_background_task(self.start_bot(user_id_str, token))

    async def init_bots(self):
        # 1. Start the Master Bot from settings
        self._init_master_bot()

        # 2. Fetch all users with tokens from API
        max_retries = 5
        for attempt in range(max_retries):
            try:
                users = await self._fetch_users_with_bots()
                if users is not None:
                    if users:
                        self._start_user_bots(users)
                    else:
                        logger.info("No users with Telegram bots configured")
                    break

                logger.error(
                    f"Failed to fetch users (Attempt {attempt + 1}/{max_retries})"
                )
            except Exception as e:
                logger.exception(
                    f"Error initializing bots (Attempt {attempt + 1}/{max_retries}): {e}"
                )

            await asyncio.sleep(5)  # Wait for API to come online


bot_manager = BotManager()


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "openclaw", "active_bots": len(bot_manager.apps)}


@app.post("/refresh-bot/{user_id}")
async def refresh_bot(user_id: str, background_tasks: BackgroundTasks):
    # Fetch token from main API
    try:
        # Internal call to get user info (we'll need to make sure this returns the token)
        # Note: In production, this should be internal-only and secure
        headers = {}
        if settings.INTERNAL_API_TOKEN:
            headers["Authorization"] = f"Bearer {settings.INTERNAL_API_TOKEN}"

        response = await bot_manager.http.get(
            f"{settings.API_URL}/api/v1/auth/verify-telegram-internal/{user_id}",
            headers=headers,
            timeout=5.0,
        )
        if response.status_code == 200:
            user_data = response.json()
            token = user_data.get("telegram_token")
            if token:
                background_tasks.add_task(bot_manager.start_bot, user_id, token)
                return {
                    "status": "success",
                    "message": f"Refreshing bot for user {user_id}",
                }
            else:
                background_tasks.add_task(bot_manager.stop_bot, user_id)
                return {
                    "status": "success",
                    "message": f"Stopping bot for user {user_id} (no token)",
                }
        return {"status": "error", "message": "User not found or API error"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Twilio Webhook for incoming WhatsApp messages.
    """
    try:
        # Twilio sends data as form-urlencoded
        form_data = await request.form()
        incoming_msg = form_data.get("Body", "")
        sender_id = form_data.get("From", "")  # Format: "whatsapp:+1234567890"

        logger.info(f"Incoming WhatsApp from {sender_id}: {incoming_msg}")

        # The agent expects a somewhat generic ID and text.
        # It handles DB verification via API.
        response_text = await agent.process_message(sender_id, incoming_msg)

        # Twilio expects an XML response (TwiML)
        # We manually construct simple XML to avoid requiring the full twilio SDK payload
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Message>{response_text}</Message>
        </Response>"""

        return Response(content=twiml, media_type="application/xml")

    except Exception as e:
        logger.exception(f"WhatsApp Webhook Error: {e}")
        # Return generic error in TwiML
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Message>⚠️ Agent encountered an internal error processing your WhatsApp message.</Message>
        </Response>"""
        return Response(content=twiml, media_type="application/xml")


class BroadcastRequest(BaseModel):
    user_ids: list[str]
    message: str
    platform_hint: Optional[str] = None


@app.post("/broadcast")
async def broadcast_message(
    request: BroadcastRequest, background_tasks: BackgroundTasks
):
    """
    Triggers an outbound message to specific users via the MessageDispatcher.
    """
    try:
        success_count = 0
        for uid in request.user_ids:
            # We fire these off in the background to avoid blocking the API response
            # In a heavy environment, we'd use Celery for this.
            background_tasks.add_task(
                base_dispatcher_service.broadcast_to_user,
                uid,
                request.message,
                request.platform_hint,
            )
            success_count += 1

        return {
            "status": "success",
            "message": f"Broadcast queued for {success_count} users.",
        }
    except Exception as e:
        logger.exception(f"Broadcast Error: {e}")
        return {"status": "error", "message": str(e)}


class ToolRequest(BaseModel):
    tool: str
    params: dict = {}
    internal_token: str | None = None


@app.post("/execute-tool")
async def execute_tool(request: ToolRequest):
    """
    Execute an OpenClaw tool directly (Internal Only).
    """
    # Verify internal token
    if settings.INTERNAL_API_TOKEN and request.internal_token != settings.INTERNAL_API_TOKEN:
        return {"status": "error", "message": "Unauthorized internal call"}

    try:
        result = await agent.execute_tool({
            "tool": request.tool,
            "params": request.params
        })
        return {"status": "success", "result": result}
    except Exception as e:
        logger.exception(f"Tool Execution Error: {e}")
        return {"status": "error", "message": str(e)}


@app.on_event("startup")
async def startup_event():
    bot_manager.run_background_task(bot_manager.init_bots())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
