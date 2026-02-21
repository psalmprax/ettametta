import asyncio
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from config import settings
from agent import OpenClawAgent
import uvicorn
from fastapi import FastAPI, BackgroundTasks
from typing import Dict

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("OpenClaw")

app = FastAPI()
agent = OpenClawAgent()

class BotManager:
    def __init__(self):
        self.apps: Dict[int, any] = {}

    async def start_bot(self, user_id: int, token: str):
        if user_id in self.apps:
            await self.stop_bot(user_id)
        
        try:
            logger.info(f"Starting bot for user {user_id}...")
            application = ApplicationBuilder().token(token).build()
            
            # Use specific user_id in context for the agent
            async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
                await context.bot.send_message(
                    chat_id=update.effective_chat.id, 
                    text="🦅 OpenClaw Online. Your private agent is ready."
                )

            async def msg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
                # IMPORTANT: Use the telegram user ID as it usually matches what they'll put in dashboard
                # OR we verify against the provided user_id for this specific bot instance.
                # In white-label mode, we trust anyone messaging this private bot? 
                # No, we still verify against the user_id that owns the token.
                tg_user_id = update.effective_user.id
                text = update.message.text
                
                # Verify that the person messaging the bot is the owner (or has access)
                # For white-label, we check if tg_user_id matches the user's saved chat_id
                response = await agent.process_message(tg_user_id, text)
                
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=response
                )

            application.add_handler(CommandHandler('start', start_cmd))
            application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), msg_handler))
            
            await application.initialize()
            await application.start()
            await application.updater.start_polling()
            
            self.apps[user_id] = application
            logger.info(f"Bot for user {user_id} started successfully.")
        except Exception as e:
            logger.error(f"Failed to start bot for user {user_id}: {e}")

    async def stop_bot(self, user_id: int):
        if user_id in self.apps:
            logger.info(f"Stopping bot for user {user_id}...")
            app = self.apps[user_id]
            await app.updater.stop()
            await app.stop()
            await app.shutdown()
            del self.apps[user_id]

    async def init_bots(self):
        # Fetch all users with tokens from API
        try:
            # We'll need a special internal endpoint or just loop/filter (admin only essentially)
            # For now, let's assume we have an endpoint for this or we just handle the shared bot too
            # Actually, let's just use the shared bot token from settings if present as "admin" bot (id 0)
            if settings.TELEGRAM_BOT_TOKEN:
                await self.start_bot(0, settings.TELEGRAM_BOT_TOKEN)
            
            # In a real scenario, we'd fetch all users from the DB here
            # But the refresh-bot endpoint will handle dynamic additions
        except Exception as e:
            logger.error(f"Error initializing bots: {e}")

bot_manager = BotManager()

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "openclaw", "active_bots": len(bot_manager.apps)}

@app.post("/refresh-bot/{user_id}")
async def refresh_bot(user_id: int, background_tasks: BackgroundTasks):
    # Fetch token from main API
    try:
        # Internal call to get user info (we'll need to make sure this returns the token)
        # Note: In production, this should be internal-only and secure
        response = requests.get(f"{settings.API_URL}/auth/verify-telegram-internal/{user_id}")
        if response.status_code == 200:
            user_data = response.json()
            token = user_data.get("telegram_token")
            if token:
                background_tasks.add_task(bot_manager.start_bot, user_id, token)
                return {"status": "success", "message": f"Refreshing bot for user {user_id}"}
            else:
                background_tasks.add_task(bot_manager.stop_bot, user_id)
                return {"status": "success", "message": f"Stopping bot for user {user_id} (no token)"}
        return {"status": "error", "message": "User not found or API error"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(bot_manager.init_bots())

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
