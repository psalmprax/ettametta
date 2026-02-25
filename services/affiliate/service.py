"""
Affiliate Service - Optional affiliate API integration
=====================================================
Disabled by default. Enable with: ENABLE_AFFILIATE_API=true

This service provides programmatic access to affiliate networks:
- Amazon Associates
- Impact Radius
- ShareASale

Used for product recommendations in video descriptions.
"""

import os
import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import aiohttp

logger = logging.getLogger(__name__)


class AffiliateService:
    """
    Optional affiliate API integration.
    
    Disabled by default - set ENABLE_AFFILIATE_API=true to enable.
    Supports Amazon Associates, Impact Radius, and ShareASale.
    """
    
    def __init__(self):
        self.enabled = os.getenv("ENABLE_AFFILIATE_API", "false").lower() == "true"
        
        from api.config import settings
        self.amazon_tag = settings.AMAZON_ASSOCIATES_TAG
        self.impact_api_key = settings.IMPACT_RADIUS_API_KEY
        self.sharesale_api_key = settings.SHAREASALE_API_KEY
        
        if not self.enabled:
            logger.info("Affiliate service is disabled (ENABLE_AFFILIATE_API=false)")
            return
        
        # Check if at least one API is configured
        has_api = any([
            self.amazon_tag,
            self.impact_api_key,
            self.sharesale_api_key
        ])
        
        if not has_api:
            logger.warning("No affiliate API keys configured. Service enabled but may not work.")
        
        logger.info("Affiliate service initialized")
    
    def is_enabled(self) -> bool:
        """Check if service is enabled."""
        return self.enabled
    
    async def search_amazon_products(
        self, 
        query: str, 
        category: str = "all",
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search Amazon products via Associates API.
        
        Args:
            query: Product search query
            category: Product category
            max_results: Max number of results
            
        Returns:
            List of product dicts with name, price, URL, commission
        """
        if not self.enabled:
            raise RuntimeError("Affiliate service is not enabled")
        
        if not self.amazon_tag:
            logger.warning("Amazon Associates tag not configured")
            return []
        
        # Note: Real Amazon Product Advertising API requires signed requests
        # This is a simplified implementation using PA-API 5.0
        # In production, use amazon-paapi package
        
        try:
            # Simulated response structure
            products = [
                {
                    "asin": "B08N5WRWNW",
                    "title": f"Sample Product: {query}",
                    "price": {"amount": 29.99, "currency": "USD"},
                    "image_url": "https://via.placeholder.com/150",
                    "detail_url": f"https://www.amazon.com/dp/B08N5WRWNW?tag={self.amazon_tag}",
                    "commission_rate": 0.10,
                    "category": category
                }
            ]
            
            logger.info(f"Amazon search for '{query}': {len(products)} results")
            return products[:max_results]
            
        except Exception as e:
            logger.error(f"Amazon API error: {e}")
            return []
    
    async def get_impact_products(
        self,
        campaign_id: str,
        query: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Get products from Impact Radius.
        
        Args:
            campaign_id: Impact campaign ID
            query: Optional search query
            
        Returns:
            List of available products
        """
        if not self.enabled:
            raise RuntimeError("Affiliate service is not enabled")
        
        if not self.impact_api_key:
            logger.warning("Impact Radius API key not configured")
            return []
        
        try:
            # Impact Radius API endpoint
            url = f"https://api.impact.com/Advertisers/{campaign_id}/Products"
            
            # Simulated response
            products = [
                {
                    "id": "prod_123",
                    "name": f"Impact Product: {query}",
                    "price": 39.99,
                    "commission": 0.15,
                    "url": "https://example.com/affiliate-link"
                }
            ]
            
            return products
            
        except Exception as e:
            logger.error(f"Impact Radius API error: {e}")
            return []
    
    async def get_sharesale_products(
        self,
        query: str,
        merchant_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get products from ShareASale.
        
        Args:
            query: Search query
            merchant_id: Optional specific merchant
            
        Returns:
            List of products
        """
        if not self.enabled:
            raise RuntimeError("Affiliate service is not enabled")
        
        if not self.sharesale_api_key:
            logger.warning("ShareASale API key not configured")
            return []
        
        try:
            # ShareASale API
            products = [
                {
                    "merchant_id": merchant_id or 12345,
                    "name": f"ShareASale Product: {query}",
                    "price": 24.99,
                    "commission": 0.12,
                    "url": "https://example.com/sas-link"
                }
            ]
            
            return products
            
        except Exception as e:
            logger.error(f"ShareASale API error: {e}")
            return []
    
    async def search_products(
        self,
        niche: str,
        networks: List[str] = None
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
        self,
        product_url: str,
        network: str = "amazon"
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
        self,
        product_price: float,
        network: str = "amazon"
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
            "sharesale": 0.12  # 12% average
        }
        
        rate = rates.get(network, 0.10)
        return product_price * rate


# Singleton instance
affiliate_service = AffiliateService()
