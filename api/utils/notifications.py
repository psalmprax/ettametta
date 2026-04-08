import httpx
from typing import Optional


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

    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)
        return response.json()


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

    auth = (account_sid, auth_token)
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data, auth=auth)
        return response.json()</content>
<parameter name="filePath">api/utils/notifications.py