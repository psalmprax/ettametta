import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.services.monetization.auto_merch import AutoMerchService
from src.services.affiliate.service import AffiliateService
from src.services.monetization.strategies.crypto import CryptoStrategy
from src.services.monetization.strategies.lead_gen import LeadGenStrategy
from src.api.config import settings

@pytest.mark.anyio
class TestHardenedAutoMerch:
    async def test_publish_to_pod_mock_fallback(self):
        """Test that AutoMerch refuses to use mock in production logic if API key is missing."""
        service = AutoMerchService()
        with patch.object(settings, "PRINTFUL_API_KEY", ""):
            # We now correctly raise ValueError, proving no silent mock fallback
            with pytest.raises(ValueError) as exc:
                await service._publish_to_pod("Test T-Shirt", "https://example.com/design.png")
            assert "Printful API Key not configured" in str(exc.value)

    async def test_publish_to_pod_real_api_structure(self):
        """Test that AutoMerch sends the correct payload to Printful."""
        service = AutoMerchService()
        mock_api_key = "test_printful_key"
        
        with patch.object(settings, "PRINTFUL_API_KEY", mock_api_key):
            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = MagicMock(
                    status_code=201, 
                    json=lambda: {"result": {"id": 12345, "name": "Test T-Shirt"}}
                )
                
                result = await service._publish_to_pod("Test T-Shirt", "https://example.com/design.png")
                
                assert result is not None
                assert result["id"] == "12345"
                assert result["status"] == "published"

@pytest.mark.anyio
class TestHardenedAffiliate:
    async def test_amazon_paapi_structure(self):
        """Test Amazon PA-API request structure."""
        service = AffiliateService()
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"SearchResult": {"Items": [{"ASIN": "B08N5WRWNW", "ItemInfo": {"Title": {"DisplayValue": "Test Product"}}}]}}
            )
            
            with patch.object(service, 'amazon_tag', 'tag-20'):
                result = await service._search_paapi("key", "tag", "laptop", "Electronics", 1)
                assert len(result) == 1
                assert result[0]["asin"] == "B08N5WRWNW"

    async def test_impact_radius_structure(self):
        """Test Impact Radius request structure."""
        service = AffiliateService()
        # Ensure service is enabled and has a key
        service.enabled = True
        service.impact_api_key = "test_secret"
        
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"Ads": [{"Id": "impact_123", "Name": "Impact Laptop"}]}
            )
            
            result = await service.get_impact_products("campaign_1", "laptop")
            assert len(result) > 0
            assert result[0]["id"] == "impact_123"

@pytest.mark.anyio
class TestHardenedCrypto:
    async def test_wallet_validation(self):
        """Test BTC and ETH wallet validation logic."""
        strategy = CryptoStrategy()
        
        # Valid BTC
        assert await strategy.validate_address("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "BTC") is True
        # Valid ETH
        assert await strategy.validate_address("0x742d35Cc6634C0532925a3b844Bc454e4438f44e", "ETH") is True
        # Invalid
        assert await strategy.validate_address("invalid_address", "BTC") is False

@pytest.mark.anyio
class TestHardenedLeadGen:
    async def test_mailchimp_subscription_logic(self):
        """Test Mailchimp subscription request structure."""
        strategy = LeadGenStrategy()
        mock_email = "test@example.com"
        
        with patch("api.config.settings.MAILCHIMP_API_KEY", "test-us19"):
            with patch("api.config.settings.MAILCHIMP_LIST_ID", "list_123"):
                with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                    mock_post.return_value = MagicMock(status_code=200)
                    
                    success = await strategy.subscribe_lead(mock_email, "AI")
                    assert success is True
                    
                    # Verify URL contains datacenter
                    args, kwargs = mock_post.call_args
                    assert "us19.api.mailchimp.com" in args[0]
                    assert kwargs["json"]["email_address"] == mock_email
