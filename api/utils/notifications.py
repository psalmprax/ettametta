import httpx
from typing import Optional
from sqlalchemy.orm import Session
from api.utils.database import get_db


async def send_telegram_message(bot_token: str, chat_id: str, message: str) -> dict:
    """
    Send a message via Telegram Bot API.

    Args:
        bot_token: Telegram bot token
        chat_id: Chat ID to send message to
        message: Message text

    Returns:
        Response JSON from Telegram API
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            return response.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def send_whatsapp_message(
    account_sid: str, auth_token: str, from_number: str, to_number: str, message: str
) -> dict:
    """
    Send a message via WhatsApp using Twilio API.

    Args:
        account_sid: Twilio account SID
        auth_token: Twilio auth token
        from_number: Twilio WhatsApp number (without whatsapp: prefix)
        to_number: Recipient WhatsApp number (without whatsapp: prefix)
        message: Message text

    Returns:
        Response JSON from Twilio API
    """
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    data = {
        "From": f"whatsapp:{from_number}",
        "To": f"whatsapp:{to_number}",
        "Body": message,
    }

    try:
        auth = (account_sid, auth_token)
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, auth=auth)
            return response.json()
    except Exception as e:
        return {"error": str(e)}


async def configure_telegram_bot(user_id: int, chat_id: str) -> dict:
    """
    Configure Telegram bot for user by sending a confirmation message.

    Args:
        user_id: User ID
        chat_id: Telegram chat ID

    Returns:
        Response from Telegram API
    """
    from api.config import settings as app_settings

    bot_token = app_settings.TELEGRAM_BOT_TOKEN
    message = "Your Telegram notifications are configured."
    return await send_telegram_message(bot_token, chat_id, message)


async def configure_whatsapp_bot(user_id: int, number: str) -> dict:
    """
    Configure WhatsApp bot for user by sending a confirmation message.

    Args:
        user_id: User ID
        number: WhatsApp number

    Returns:
        Response from Twilio API
    """
    from api.config import settings as app_settings

    account_sid = app_settings.TWILIO_ACCOUNT_SID
    auth_token = app_settings.TWILIO_AUTH_TOKEN
    from_number = app_settings.TWILIO_WHATSAPP_NUMBER
    message = "Your WhatsApp notifications are configured."
    return await send_whatsapp_message(
        account_sid, auth_token, from_number, number, message
    )
