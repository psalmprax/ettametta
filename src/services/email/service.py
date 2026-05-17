"""
Email Service - Transactional and marketing email delivery
==========================================================
Provides unified email delivery via Mailchimp, ConvertKit, or SMTP fallback.
Handles welcome emails, password resets, notifications, and marketing campaigns.
"""

import os
import logging
import httpx
from typing import Any
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class EmailProvider(ABC):
    """Abstract base class for email providers."""

    @abstractmethod
    async def send_transactional(
        self, to: str, subject: str, html_content: str, text_content: str | None = None
    ) -> bool:
        pass

    @abstractmethod
    async def add_subscriber(self, email: str, tags: list[str] | None = None) -> bool:
        pass

    @abstractmethod
    async def remove_subscriber(self, email: str) -> bool:
        pass


class MailchimpProvider(EmailProvider):
    """Mailchimp integration for transactional and marketing emails."""

    def __init__(self, api_key: str, list_id: str | None = None):
        self.api_key = api_key
        self.list_id = list_id
        self.datacenter = api_key.split("-")[-1]
        self.base_url = f"https://{self.datacenter}.api.mailchimp.com/3.0"
        self.headers = {
            "Authorization": f"apikey {api_key}",
            "Content-Type": "application/json",
        }

    async def send_transactional(
        self, to: str, subject: str, html_content: str, text_content: str | None = None
    ) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=self.headers,
                    json={
                        "message": {
                            "to": [{"email": to}],
                            "subject": subject,
                            "html": html_content,
                            "text": text_content or html_content,
                        }
                    },
                    timeout=30.0,
                )
                if response.status_code in (200, 201):
                    logger.info(f"Mailchimp email sent to {to}")
                    return True
                logger.error(f"Mailchimp send failed: {response.status_code} {response.text}")
                return False
        except Exception as e:
            logger.error(f"Mailchimp send error: {e}")
            return False

    async def add_subscriber(self, email: str, tags: list[str] | None = None) -> bool:
        if not self.list_id:
            logger.error("Mailchimp list_id not configured")
            return False
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/lists/{self.list_id}/members",
                    headers=self.headers,
                    json={
                        "email_address": email,
                        "status": "subscribed",
                        "tags": tags or [],
                    },
                    timeout=30.0,
                )
                if response.status_code in (200, 201, 400):
                    logger.info(f"Mailchimp subscriber added: {email}")
                    return True
                logger.error(f"Mailchimp subscribe failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Mailchimp subscribe error: {e}")
            return False

    async def remove_subscriber(self, email: str) -> bool:
        if not self.list_id:
            return False
        try:
            import hashlib
            subscriber_hash = hashlib.md5(email.lower().encode()).hexdigest()
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/lists/{self.list_id}/members/{subscriber_hash}",
                    headers=self.headers,
                    json={"status": "unsubscribed"},
                    timeout=30.0,
                )
                return response.status_code in (200, 201)
        except Exception as e:
            logger.error(f"Mailchimp unsubscribe error: {e}")
            return False


class ConvertKitProvider(EmailProvider):
    """ConvertKit integration for email marketing."""

    def __init__(self, api_key: str, form_id: str | None = None):
        self.api_key = api_key
        self.form_id = form_id
        self.base_url = "https://api.convertkit.com/v3"

    async def send_transactional(
        self, to: str, subject: str, html_content: str, text_content: str | None = None
    ) -> bool:
        logger.warning("ConvertKit does not support direct transactional email via API")
        return False

    async def add_subscriber(self, email: str, tags: list[str] | None = None) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                data = {"api_key": self.api_key, "email": email}
                if tags:
                    data["tags"] = tags
                if self.form_id:
                    endpoint = f"{self.base_url}/forms/{self.form_id}/subscribe"
                else:
                    endpoint = f"{self.base_url}/subscribe"
                response = await client.post(endpoint, json=data, timeout=30.0)
                if response.status_code in (200, 201):
                    logger.info(f"ConvertKit subscriber added: {email}")
                    return True
                logger.error(f"ConvertKit subscribe failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"ConvertKit subscribe error: {e}")
            return False

    async def remove_subscriber(self, email: str) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/subscribers",
                    params={"api_key": self.api_key, "email": email},
                    timeout=30.0,
                )
                return response.status_code in (200, 201)
        except Exception as e:
            logger.error(f"ConvertKit unsubscribe error: {e}")
            return False


class EmailService:
    """
    Unified email service with provider abstraction.
    Supports Mailchimp, ConvertKit, and SMTP fallback.
    """

    def __init__(self):
        from src.api.config import settings

        self.settings = settings
        self.provider: EmailProvider | None = None
        self._init_provider()

    def _init_provider(self):
        if self.settings.MAILCHIMP_API_KEY:
            self.provider = MailchimpProvider(
                api_key=self.settings.MAILCHIMP_API_KEY,
                list_id=self.settings.MAILCHIMP_LIST_ID,
            )
            logger.info("Email service initialized with Mailchimp")
        elif self.settings.CONVERTKIT_API_KEY:
            self.provider = ConvertKitProvider(
                api_key=self.settings.CONVERTKIT_API_KEY,
            )
            logger.info("Email service initialized with ConvertKit")
        else:
            logger.warning("No email provider configured. Email service disabled.")

    def is_enabled(self) -> bool:
        return self.provider is not None

    async def send_welcome_email(self, email: str, username: str) -> bool:
        if not self.is_enabled():
            return False
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1>Welcome to Ettametta, {username}!</h1>
            <p>Your account has been created successfully.</p>
            <p>Get started by exploring our features and creating your first viral content.</p>
            <p>Best regards,<br>The Ettametta Team</p>
        </body>
        </html>
        """
        return await self.provider.send_transactional(
            to=email,
            subject="Welcome to Ettametta!",
            html_content=html,
            text_content=f"Welcome to Ettametta, {username}! Your account has been created successfully.",
        )

    async def send_password_reset_email(self, email: str, reset_token: str) -> bool:
        if not self.is_enabled():
            return False
        reset_url = f"{self.settings.PRODUCTION_DOMAIN}/reset-password?token={reset_token}"
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1>Password Reset Request</h1>
            <p>Click the link below to reset your password:</p>
            <p><a href="{reset_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this, please ignore this email.</p>
        </body>
        </html>
        """
        return await self.provider.send_transactional(
            to=email,
            subject="Reset Your Ettametta Password",
            html_content=html,
            text_content=f"Reset your password: {reset_url}",
        )

    async def send_notification_email(
        self, email: str, subject: str, message: str
    ) -> bool:
        if not self.is_enabled():
            return False
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>{subject}</h2>
            <p>{message}</p>
            <p>Best regards,<br>The Ettametta Team</p>
        </body>
        </html>
        """
        return await self.provider.send_transactional(
            to=email,
            subject=subject,
            html_content=html,
            text_content=message,
        )

    async def subscribe_user(self, email: str, tags: list[str] | None = None) -> bool:
        if not self.is_enabled():
            return False
        return await self.provider.add_subscriber(email, tags)

    async def unsubscribe_user(self, email: str) -> bool:
        if not self.is_enabled():
            return False
        return await self.provider.remove_subscriber(email)


base_email_service = EmailService()
