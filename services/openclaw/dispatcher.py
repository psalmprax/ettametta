import logging
import requests
from config import settings

logger = logging.getLogger("MessageDispatcher")

class MessageDispatcher:
    """
    Handles outbound messaging across multiple platforms.
    Decoupled from incoming webhook/polling cycles.
    """
    
    async def broadcast_to_user(self, identifier: str, message: str, platform_hint: str = None) -> bool:
        """
        Sends an outbound message to a specific identifier.
        In a real scenario with a proper user DB connection, this would 
        derive the platform from the user's registered ID format.
        For MVP, we use formatting rules (e.g., if it starts with 'whatsapp:', use Twilio).
        """
        try:
            logger.info(f"Attempting broadcast to {identifier}")
            
            is_whatsapp = identifier.startswith("whatsapp:") or (platform_hint and platform_hint.lower() == "whatsapp")
            
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
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
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
        Assumes we have TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_NUMBER 
        in a fully realized application. Mocking the HTTP call here.
        """
        logger.info(f"[MOCK] Transmitting WhatsApp message via Twilio to {phone_number}...")
        logger.info(f"Payload: {text}")
        
        # In actual implementation:
        # auth = HTTPBasicAuth(settings.TWILIO_SID, settings.TWILIO_TOKEN)
        # payload = {"From": settings.TWILIO_WHATSAPP_NUMBER, "To": phone_number, "Body": text}
        # requests.post(f"https://api.twilio.com/2010-04-01/Accounts/.../Messages.json", data=payload, auth=auth)
        
        return True

dispatcher = MessageDispatcher()
