import os
import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "")
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")


class PayPalService:
    """
    PayPal integration for payments.
    Supports: Checkout, Subscriptions, Webhooks
    """

    def __init__(self):
        self.client_id = PAYPAL_CLIENT_ID
        self.client_secret = PAYPAL_CLIENT_SECRET
        self.mode = PAYPAL_MODE

        self.base_url = (
            "https://api-m.sandbox.paypal.com"
            if self.mode == "sandbox"
            else "https://api-m.paypal.com"
        )

        self._access_token: Optional[str] = None
        self._token_expires = 0

    async def _get_access_token(self) -> str:
        """Get PayPal access token"""
        import time

        if self._access_token and time.time() < self._token_expires:
            return self._access_token

        if not self.client_id or not self.client_secret:
            raise ValueError("PayPal credentials not configured")

        auth = httpx.BasicAuth(self.client_id, self.client_secret)
        response = httpx.post(
            f"{self.base_url}/v1/oauth2/token",
            auth=auth,
            data={"grant_type": "client_credentials"},
            headers={"Accept": "application/json"},
        )

        if response.status_code != 200:
            raise Exception(f"Failed to get PayPal token: {response.text}")

        data = response.json()
        self._access_token = data["access_token"]
        self._token_expires = time.time() + data["expires_in"] - 60

        return self._access_token

    async def create_order(
        self,
        amount: float,
        currency: str = "USD",
        description: str = "Viral Forge Purchase",
        idempotency_key: Optional[str] = None,
    ) -> dict:
        """Create a PayPal order"""
        token = await self._get_access_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        if idempotency_key:
            headers["PayPal-Request-Id"] = idempotency_key

        data = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {"currency_code": currency, "value": f"{amount:.2f}"},
                    "description": description,
                }
            ],
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v2/checkout/orders", json=data, headers=headers
            )

        if response.status_code != 201:
            raise Exception(f"Failed to create PayPal order: {response.text}")

        return response.json()

    async def capture_order(self, order_id: str) -> dict:
        """Capture an order"""
        token = await self._get_access_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v2/checkout/orders/{order_id}/capture",
                json={},
                headers=headers,
            )

        if response.status_code != 200:
            raise Exception(f"Failed to capture order: {response.text}")

        return response.json()

    async def create_subscription(
        self, plan_id: str, idempotency_key: Optional[str] = None
    ) -> dict:
        """Create a subscription"""
        token = await self._get_access_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        if idempotency_key:
            headers["PayPal-Request-Id"] = idempotency_key

        data = {
            "plan_id": plan_id,
            "application_context": {
                "brand_name": "Viral Forge",
                "landing_page": "NO_PREFERENCE",
                "user_action": "SUBSCRIBE_NOW",
                "payment_method": "PAYPAL",
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/billing/subscriptions", json=data, headers=headers
            )

        if response.status_code != 201:
            raise Exception(f"Failed to create subscription: {response.text}")

        return response.json()

    def verify_webhook_signature(
        self, body: bytes, headers: dict, webhook_id: str
    ) -> bool:
        """Verify PayPal webhook signature"""
        # Note: For production, implement proper signature verification
        # This is a simplified version
        return True


# Subscription plans
PAYPAL_PLANS = {
    "creator": {
        "product_id": "PROD_CREATOR",
        "plan_id": "PLAN_CREATOR_MONTHLY",
        "name": "Creator Plan",
        "price": 29.00,
        "description": "Creator tier subscription",
    },
    "empire": {
        "product_id": "PROD_EMPIRE",
        "plan_id": "PLAN_EMPIRE_MONTHLY",
        "name": "Empire Plan",
        "price": 99.00,
        "description": "Empire tier subscription",
    },
}


paypal_service = PayPalService()
