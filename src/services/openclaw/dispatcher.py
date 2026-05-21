import logging
import requests
from src.api.config import settings

logger = logging.getLogger("MessageDispatcher")


class MessageDispatcher:
    """
    Handles outbound messaging across multiple platforms.
    Decoupled from incoming webhook/polling cycles.
    """

    async def broadcast_to_user(
        self, identifier: str, message: str, platform_hint: str = None
    ) -> bool:
        """
        Sends an outbound message to a specific identifier.
        In a real scenario with a proper user DB connection, this would
        derive the platform from the user's registered ID format.
        For MVP, we use formatting rules (e.g., if it starts with 'whatsapp:', use Twilio).
        """
        try:
            logger.info(f"Attempting broadcast to {identifier}")

            is_whatsapp = (identifier and identifier.startswith("whatsapp:")) or (
                platform_hint and platform_hint.lower() == "whatsapp"
            )

            if is_whatsapp:
                return await self.send_whatsapp(identifier, message)
            else:
                return await self.send_telegram(identifier, message)

        except Exception as e:
            logger.error(f"Failed to dispatch message to {identifier}: {e}")
            return False

    async def send_telegram(self, chat_id: str, text: str) -> bool:
        """
        Sends an outbound message via Telegram Bot API natively.
        Uses the default bot token. For white-label, we'd need to look up the user's specific token.
        """
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("No TELEGRAM_BOT_TOKEN configured for broadcast.")
            return False

        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}

        try:
            # We use synchronous requests wrapped in async/thread context usually,
            # here we just make the synchronous call for simplicity in this MVP
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info(f"Telegram broadcast successful to {chat_id}")
                return True
            else:
                logger.error(f"Telegram broadcast failed: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Telegram API request failed: {e}")
            return False

    async def send_whatsapp(self, phone_number: str, text: str) -> bool:
        """
        Sends an outbound message via Twilio API.
        Tries the real API first, and only falls back to MOCK if credentials
        are missing or if the API call throws an exception.
        """
        if (
            settings.TWILIO_ACCOUNT_SID
            and settings.TWILIO_AUTH_TOKEN
            and settings.TWILIO_WHATSAPP_NUMBER
        ):
            try:
                from requests.auth import HTTPBasicAuth

                auth = HTTPBasicAuth(
                    settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN
                )

                # Twilio expects 'whatsapp:+123456789' format
                from_num = f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER.replace('whatsapp:', '')}"
                to_num = (
                    phone_number
                    if phone_number and phone_number.startswith("whatsapp:")
                    else f"whatsapp:{phone_number}"
                )

                payload = {"From": from_num, "To": to_num, "Body": text}
                url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"

                response = requests.post(url, data=payload, auth=auth, timeout=10)
                if response.status_code in (200, 201):
                    logger.info(
                        f"Twilio WhatsApp broadcast successful to {phone_number}"
                    )
                    return True
                else:
                    raise RuntimeError(
                        f"Twilio API rejected broadcast to {phone_number}: {response.status_code} {response.text[:200]}"
                    )
            except Exception as e:
                raise RuntimeError(
                    f"Twilio WhatsApp broadcast to {phone_number} failed: {e}"
                ) from e


base_dispatcher_service = MessageDispatcher()
