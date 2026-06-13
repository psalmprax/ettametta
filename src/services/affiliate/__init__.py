# Affiliate Service
# Any affiliate API integration - disabled by default
# Enable with: ENABLE_AFFILIATE_API=true

from .service import AffiliateService, base_affiliate_service

__all__ = ["AffiliateService", "base_affiliate_service"]
