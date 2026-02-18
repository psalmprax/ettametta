import logging
import httpx
from typing import List, Dict, Any, Optional
from api.config import settings
from api.utils.database import SessionLocal
from api.utils.models import SystemSettings, AffiliateLinkDB

class CommerceService:
    def __init__(self):
        self.logger = logging.getLogger("CommerceService")

    async def _get_shopify_creds(self, db) -> Dict[str, str]:
        """Fetches Shopify credentials from DB settings."""
        shop_url = db.query(SystemSettings).filter(SystemSettings.key == "shopify_shop_url").first()
        access_token = db.query(SystemSettings).filter(SystemSettings.key == "shopify_access_token").first()
        
        return {
            "url": shop_url.value if shop_url else None,
            "token": access_token.value if access_token else None
        }

    async def get_relevant_products(self, niche: str) -> List[Dict[str, Any]]:
        """
        Fetches products from Shopify. Falls back to database affiliate links if store is unavailable.
        """
        db = SessionLocal()
        try:
            creds = await self._get_shopify_creds(db)
            
            if creds["url"] and creds["token"] and "shpat_" in creds["token"]:
                self.logger.info(f"[Commerce] Fetching real products from Shopify: {creds['url']}")
                products = await self._fetch_from_shopify(creds["url"], creds["token"], niche)
                if products:
                    return products

            # Fallback to Affiliate Links
            self.logger.info(f"[Commerce] No active Shopify store. Falling back to affiliate links for {niche}.")
            affiliates = db.query(AffiliateLinkDB).filter(AffiliateLinkDB.niche == niche).all()
            return [{
                "id": f"aff_{a.id}",
                "name": a.product_name,
                "url": a.link,
                "price": "N/A",
                "source": "affiliate"
            } for a in affiliates]
            
        finally:
            db.close()

    async def _fetch_from_shopify(self, shop_url: str, token: str, niche: str) -> List[Dict[str, Any]]:
        """Calls Shopify Admin API to get products."""
        # Clean URL
        shop_url = shop_url.replace("https://", "").replace("http://", "").split("/")[0]
        api_url = f"https://{shop_url}/admin/api/2024-01/products.json?limit=10"
        
        # In a real scenario, we'd add 'query' or 'tag' matching niche
        # For high-velocity discovery, we'll search by the niche name
        search_url = f"{api_url}&title={niche}"
        
        headers = {
            "X-Shopify-Access-Token": token,
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(search_url, headers=headers, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    products = []
                    for p in data.get("products", []):
                        # Construct a direct product link
                        handle = p.get("handle")
                        product_url = f"https://{shop_url}/products/{handle}"
                        products.append({
                            "id": str(p.get("id")),
                            "name": p.get("title"),
                            "price": p.get("variants", [{}])[0].get("price", "0.00"),
                            "url": product_url,
                            "source": "shopify"
                        })
                    return products
                else:
                    self.logger.error(f"[Commerce] Shopify API Error: {response.status_code} - {response.text}")
                    return []
        except Exception as e:
            self.logger.error(f"[Commerce] Shopify Connection Failed: {e}")
            return []

    async def generate_checkout_link(self, product_id: str) -> str:
        """
        Generates a direct checkout URL. 
        Note: Shopify direct cart links usually prefer variant_id, but product_id handle works for routing.
        """
        # Optimized for Shopify redirection
        return f"/cart/{product_id}:1"

base_commerce_service = CommerceService()
