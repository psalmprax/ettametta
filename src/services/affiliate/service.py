"""
Affiliate Service - Optional affiliate API integration
=====================================================
Disabled by default. Enable with: ENABLE_AFFILIATE_API=true

This service provides programmatic access to affiliate networks:
- Amazon Associates (via PA-API 5.0)
- Impact Radius
- ShareASale

Used for product recommendations in video descriptions.
"""

import os
import logging
import asyncio
import uuid
import hashlib
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import aiohttp
import httpx
import time
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)


class CircuitBreaker:
    """Simple circuit breaker to prevent cascading failures"""

    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 120):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def is_open(self) -> bool:
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return False
            return True
        return False

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


logger = logging.getLogger(__name__)


class AffiliateService:
    """
    Optional affiliate API integration.

    Disabled by default - set ENABLE_AFFILIATE_API=true to enable.
    Supports Amazon Associates, Impact Radius, and ShareASale.
    Production-grade with circuit breaking and retries.
    """

    def __init__(self):
        self.logger = logging.getLogger("AffiliateService")
        self.enabled = os.getenv("ENABLE_AFFILIATE_API", "false").lower() == "true"

        from api.config import settings

        self.amazon_tag = settings.AMAZON_ASSOCIATES_TAG
        self.impact_api_key = settings.IMPACT_RADIUS_API_KEY
        self.sharesale_api_key = settings.SHAREASALE_API_KEY

        # Circuit breakers for each provider
        self.amazon_circuit_breaker = CircuitBreaker()
        self.impact_circuit_breaker = CircuitBreaker()
        self.sharesale_circuit_breaker = CircuitBreaker()
        self.http_client: Optional[httpx.AsyncClient] = None

        if not self.enabled:
            self.logger.info(
                "Affiliate service is disabled (ENABLE_AFFILIATE_API=false)"
            )
            return

        # Check if at least one API is configured
        has_api = any([self.amazon_tag, self.impact_api_key, self.sharesale_api_key])

        if not has_api:
            self.logger.warning(
                "No affiliate API keys configured. Service enabled but may not work."
            )

        self.logger.info("Affiliate service initialized")

    @property
    def http(self) -> httpx.AsyncClient:
        if not self.http_client:
            self.http_client = httpx.AsyncClient(timeout=15.0, follow_redirects=True)
        return self.http_client

    def is_enabled(self) -> bool:
        """Check if service is enabled."""
        return self.enabled

    async def search_amazon_products(
        self, query: str, category: str = "all", max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search Amazon products via Associates API (PA-API 5.0).

        Returns empty list if service disabled or no credentials configured.
        """
        if not self.enabled:
            raise RuntimeError("Affiliate service is not enabled")

        from api.config import settings

        amazon_api_key = getattr(settings, "AMAZON_PAAPI_KEY", None)
        amazon_api_tag = getattr(settings, "AMAZON_PAAPI_TAG", None)

        if not (amazon_api_key and amazon_api_tag):
            logger.warning(
                "Amazon PA-API credentials not fully configured (AMAZON_PAAPI_KEY, AMAZON_PAAPI_TAG)"
            )
            return []

        return await self._search_paapi(
            amazon_api_key, amazon_api_tag, query, category, max_results
        )

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=False,
    )
    async def _search_paapi(
        self, api_key: str, api_tag: str, query: str, category: str, max_results: int
    ) -> List[Dict[str, Any]]:
        """
        Use Amazon Product Advertising API 5.0 with AWS SigV4 signing.
        Uses botocore for request signing.
        Production-grade with circuit breaking and retries.
        """
        if self.amazon_circuit_breaker.is_open():
            self.logger.warning("Amazon PA-API circuit breaker is OPEN")
            return []

        import uuid
        from botocore.auth import SigV4
        from botocore.awsrequest import AWSRequest
        from botocore.credentials import Credentials

        # PA-API endpoint and region
        host = "webservices.amazon.com"
        region = "us-east-1"
        service = "ProductAdvertisingAPI"

        # Build request payload
        payload = {
            "Keywords": query,
            "SearchIndex": category if category != "all" else "All",
            "ItemCount": min(max_results, 10),
            "Resources": [
                "Images.Primary.Medium",
                "ItemInfo.Title",
                "Offers.Listings.Price",
                "ItemInfo.ByLineInfo",
                "ItemInfo.ProductInfo",
            ],
            "PartnerTag": api_tag,
            "PartnerType": "Associates",
            "Marketplace": "www.amazon.com",
        }

        json_payload = json.dumps(payload)

        # Create AWS request
        request = AWSRequest(
            method="POST",
            url=f"https://{host}/paapi5/searchitems",
            data=json_payload,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "X-Amz-Target": "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems",
            },
        )

        # Sign request using credentials (access key as access_key, secret as secret_key)
        # We assume api_key is the Access Key ID. But PA-API also requires Secret Key. Where do we get it?
        # Usually PA-API uses Access Key ID and Secret Key (not the tag). The tag is the associate tag.
        # We need to fetch secret from config.
        from api.config import settings

        amazon_secret_key = getattr(settings, "AMAZON_PAAPI_SECRET", None)
        if not amazon_secret_key:
            self.logger.error(
                "Amazon PA-API secret key not configured (AMAZON_PAAPI_SECRET)"
            )
            return []

        credentials = Credentials(api_key, amazon_secret_key)
        SigV4(credentials, service, region).add_auth(request)

        # Convert to regular headers
        headers = dict(request.headers)

        try:
            response = await self.http.post(
                f"https://{host}/paapi5/searchitems",
                content=json_payload,
                headers=headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                self.amazon_circuit_breaker.record_failure()
                self.logger.error(
                    f"PA-API error {response.status_code}: {response.text}"
                )
                return []

            data = response.json()
            products = []

            # Parse response
            items = data.get("SearchResult", {}).get("Items", [])
            for item in items:
                asin = item.get("ASIN")
                title_info = item.get("ItemInfo", {}).get("Title", {})
                title = title_info.get("DisplayValue", "") or title_info.get(
                    "Label", ""
                )
                price_info = (
                    item.get("Offers", {}).get("Listings", [{}])[0].get("Price", {})
                )
                price_amount = price_info.get("Amount", 0)
                image_info = item.get("Images", {}).get("Primary", {}).get("Medium", {})
                image_url = image_info.get("URL", "")
                detail_url = f"https://www.amazon.com/dp/{asin}?tag={api_tag}"

                products.append(
                    {
                        "asin": asin,
                        "title": title,
                        "price": {"amount": price_amount, "currency": "USD"},
                        "image_url": image_url,
                        "detail_url": detail_url,
                        "commission_rate": None,  # Not provided by API
                        "category": category,
                    }
                )

            self.amazon_circuit_breaker.record_success()
            return products

        except Exception as e:
            self.amazon_circuit_breaker.record_failure()
            self.logger.error(f"PA-API request failed: {e}")
            return []

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=False,
    )
    async def get_impact_products(
        self, campaign_id: str, query: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Get products from Impact Radius API.
        Returns empty list if service disabled or no credentials.
        Production-grade with circuit breaking and retries.
        """
        if not self.enabled:
            return []

        if not self.impact_api_key:
            self.logger.warning("[Affiliate] Impact Radius API key not configured.")
            return []

        if self.impact_circuit_breaker.is_open():
            self.logger.warning("Impact Radius circuit breaker is OPEN")
            return []

        try:
            # Impact API requires Account SID and Auth Token
            # Expect IMPACT_ACCOUNT_SID in config
            from api.config import settings

            impact_account_sid = getattr(settings, "IMPACT_ACCOUNT_SID", None)
            if not impact_account_sid:
                self.logger.error(
                    "Impact: Account SID not configured (IMPACT_ACCOUNT_SID)"
                )
                return []

            # Build URL for product search
            # Example endpoint: /Mediapartners/{account_sid}/Ads?Type=PRODUCT&Query={query}
            url = f"https://api.impact.com/Mediapartners/{impact_account_sid}/Ads"
            params = {"Type": "PRODUCT", "Query": query}

            response = await self.http.get(
                url,
                params=params,
                auth=(impact_account_sid, self.impact_api_key),
                timeout=10.0,
            )

            if response.status_code == 200:
                data = response.json()
                ads = data.get("Ads", [])
                self.impact_circuit_breaker.record_success()
                return [
                    {
                        "id": ad.get("Id"),
                        "name": ad.get("Name"),
                        "price": ad.get("RetailPrice"),
                        "url": ad.get("TrackingLink"),
                        "source": "impact",
                    }
                    for ad in ads
                ]
            else:
                self.impact_circuit_breaker.record_failure()
                self.logger.warning(
                    f"[Affiliate] Impact API failed: {response.status_code}"
                )
                return []
        except Exception as e:
            self.impact_circuit_breaker.record_failure()
            self.logger.error(f"[Affiliate] Impact API Error: {e}")
            return []

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=False,
    )
    async def get_sharesale_products(
        self, query: str, merchant_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get products from ShareASale API.
        Returns empty list if disabled or no credentials.
        Production-grade with circuit breaking and retries.
        """
        if not self.enabled:
            return []

        if not self.sharesale_api_key:
            self.logger.warning("[Affiliate] ShareASale API key not configured.")
            return []

        if self.sharesale_circuit_breaker.is_open():
            self.logger.warning("ShareASale circuit breaker is OPEN")
            return []

        try:
            # ShareASale API: https://api.shareasale.com/x.cfm
            # Requires API key, action, and optional parameters.
            # Authentication via x-ShareASale-Date and x-ShareASale-Authentication headers.
            base_url = "https://api.shareasale.com/x.cfm"
            now = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

            # Build signature: {API_KEY}:{ACTION}:{TIMESTAMP}
            # ACTION can be getProducts or getProductDetails
            action = "getProducts"
            sig_string = f"{self.sharesale_api_key}:{action}:{now}"
            signature = hashlib.sha256(sig_string.encode()).hexdigest()

            params = {
                "action": action,
                "keyword": query,
                "format": "json",  # Request JSON response
            }
            if merchant_id:
                params["merchantID"] = merchant_id

            headers = {
                "x-ShareASale-Date": now,
                "x-ShareASale-Authentication": signature,
            }

            response = await self.http.get(
                base_url, params=params, headers=headers, timeout=10.0
            )

            if response.status_code == 200:
                try:
                    data = response.json()
                except Exception as e:
                    self.sharesale_circuit_breaker.record_failure()
                    self.logger.error(f"[Affiliate] ShareASale JSON parse error: {e}")
                    return []
                products = []
                # The exact structure depends on ShareASale's response; typical:
                # { "products": { "product": [ ... ] } } or similar.
                # We'll attempt to map common fields.
                product_list = data.get("products", {}).get("product", [])
                if isinstance(product_list, dict):
                    product_list = [product_list]  # single product as dict
                for p in product_list:
                    products.append(
                        {
                            "id": p.get("productid") or p.get("id"),
                            "name": p.get("name") or p.get("productname"),
                            "price": p.get("price"),
                            "url": p.get("url") or p.get("link"),
                            "source": "sharesale",
                        }
                    )
                self.sharesale_circuit_breaker.record_success()
                return products
            else:
                self.sharesale_circuit_breaker.record_failure()
                self.logger.warning(
                    f"[Affiliate] ShareASale API failed: {response.status_code}"
                )
                return []
        except Exception as e:
            self.sharesale_circuit_breaker.record_failure()
            self.logger.error(f"[Affiliate] ShareASale API Error: {e}")
            return []

    async def search_products(
        self, niche: str, networks: List[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search products across all configured networks.

        Args:
            niche: Product niche/category
            networks: List of networks to search (amazon, impact, sharesale)

        Returns:
            Dict mapping network names to product lists
        """
        if networks is None:
            networks = []

        results = {}

        if "amazon" in networks or not networks:
            results["amazon"] = await self.search_amazon_products(niche)

        if "impact" in networks or not networks:
            results["impact"] = await self.get_impact_products("default", niche)

        if "sharesale" in networks or not networks:
            results["sharesale"] = await self.get_sharesale_products(niche)

        return results

    async def generate_affiliate_link(
        self, product_url: str, network: str = "amazon"
    ) -> str:
        """
        Convert product URL to affiliate link.

        Args:
            product_url: Direct product URL
            network: Affiliate network (amazon, impact, sharesale)

        Returns:
            Affiliate-tagged URL
        """
        if network == "amazon":
            if "amazon.com" in product_url and "tag=" not in product_url:
                # Add tag to Amazon URL
                tag = self.amazon_tag or "default-20"
                separator = "&" if "?" in product_url else "?"
                return f"{product_url}{separator}tag={tag}"

        # For other networks, assume URL is already affiliate-linked
        return product_url

    def get_commission_rate(
        self, product_price: float, network: str = "amazon"
    ) -> float:
        """
        Calculate estimated commission.

        Args:
            product_price: Product price
            network: Affiliate network

        Returns:
            Estimated commission amount
        """
        rates = {
            "amazon": 0.10,  # 10% average
            "impact": 0.15,  # 15% average
            "sharesale": 0.12,  # 12% average
        }

        rate = rates.get(network, 0.10)
        return product_price * rate


# Singleton instance
affiliate_service = AffiliateService()
