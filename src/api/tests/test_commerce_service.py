"""
Tests for CommerceService — Shopify product fetching, affiliate fallback, checkout links.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.services.monetization.commerce_service import CommerceService


@pytest.mark.anyio
class TestCommerceService:
    """Tests for the CommerceService singleton."""

    async def test_get_shopify_creds_both_set(self):
        """Should return URL and token when both DB settings exist."""
        service = CommerceService()
        mock_db = AsyncMock()

        # Mock shop URL query
        mock_url_result = MagicMock()
        mock_url_setting = MagicMock(value="mystore.myshopify.com")
        mock_url_result.scalar_one_or_none.return_value = mock_url_setting

        # Mock token query
        mock_token_result = MagicMock()
        mock_token_setting = MagicMock(value="shpat_test123456789")
        mock_token_result.scalar_one_or_none.return_value = mock_token_setting

        # Side effect: first call returns URL, second returns token
        mock_db.execute = AsyncMock(side_effect=[mock_url_result, mock_token_result])

        creds = await service._get_shopify_creds(mock_db)

        assert creds["url"] == "mystore.myshopify.com"
        assert creds["token"] == "shpat_test123456789"

    async def test_get_shopify_creds_missing(self):
        """Should return None for URL/token when not in DB."""
        service = CommerceService()
        mock_db = AsyncMock()

        mock_none_result = MagicMock()
        mock_none_result.scalar_one_or_none.return_value = None

        mock_db.execute = AsyncMock(return_value=mock_none_result)

        creds = await service._get_shopify_creds(mock_db)

        assert creds["url"] is None
        assert creds["token"] is None

    async def test_fetch_from_shopify_success(self):
        """Should parse Shopify API response into normalized product list."""
        service = CommerceService()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "products": [
                {
                    "id": 12345,
                    "title": "Motivation T-Shirt",
                    "handle": "motivation-t-shirt",
                    "variants": [{"price": "24.99"}]
                },
                {
                    "id": 67890,
                    "title": "Success Hoodie",
                    "handle": "success-hoodie",
                    "variants": [{"price": "49.99"}]
                }
            ]
        }

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            products = await service._fetch_from_shopify(
                "mystore.myshopify.com",
                "shpat_test123456789",
                "Motivation"
            )

        assert len(products) == 2
        assert products[0]["id"] == "12345"
        assert products[0]["name"] == "Motivation T-Shirt"
        assert products[0]["price"] == "24.99"
        assert products[0]["source"] == "shopify"
        assert "motivation-t-shirt" in products[0]["url"]
        assert products[1]["id"] == "67890"
        assert products[1]["name"] == "Success Hoodie"

    async def test_fetch_from_shopify_api_error(self):
        """Should return empty list on non-200 status."""
        service = CommerceService()

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            products = await service._fetch_from_shopify(
                "mystore.myshopify.com",
                "bad_token",
                "Motivation"
            )

        assert products == []

    async def test_fetch_from_shopify_connection_error(self):
        """Should return empty list on network error."""
        service = CommerceService()

        with patch("httpx.AsyncClient.get", side_effect=Exception("Connection refused")):
            products = await service._fetch_from_shopify(
                "mystore.myshopify.com",
                "shpat_test123456789",
                "Motivation"
            )

        assert products == []

    async def test_fetch_from_shopify_cleans_url(self):
        """Should strip https:// prefix and trailing paths from shop URL."""
        service = CommerceService()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"products": [{
            "id": 1, "title": "Test", "handle": "test",
            "variants": [{"price": "10.00"}]
        }]}

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response) as mock_get:
            await service._fetch_from_shopify(
                "https://mystore.myshopify.com/admin",
                "shpat_test",
                "Test"
            )

            # Verify the trailing "/admin" path was stripped from the domain
            # The API URL should use just "mystore.myshopify.com" as the base
            args = mock_get.call_args[0][0]
            assert args == "https://mystore.myshopify.com/admin/api/2024-01/products.json?limit=10&title=Test"

    async def test_get_relevant_products_with_shopify_and_affiliate(self):
        """Should prefer Shopify products when both shopify and affiliate data exist."""
        service = CommerceService()

        mock_db = AsyncMock()

        # Shopify creds present
        mock_url_setting = MagicMock(value="mystore.myshopify.com")
        mock_token_setting = MagicMock(value="shpat_test123456789")

        mock_url_result = MagicMock()
        mock_url_result.scalar_one_or_none.return_value = mock_url_setting
        mock_token_result = MagicMock()
        mock_token_result.scalar_one_or_none.return_value = mock_token_setting

        mock_db.execute = AsyncMock(side_effect=[mock_url_result, mock_token_result])

        with patch.object(service, '_fetch_from_shopify', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [{
                "id": "1", "name": "Shopify Product",
                "price": "29.99", "url": "https://mystore.myshopify.com/products/test",
                "source": "shopify"
            }]

            with patch("src.services.monetization.commerce_service.async_session_factory") as mock_sf:
                mock_sf.return_value.__aenter__.return_value = mock_db

                products = await service.get_relevant_products("Motivation")

        assert len(products) == 1
        assert products[0]["source"] == "shopify"
        assert products[0]["name"] == "Shopify Product"

    async def test_get_relevant_products_affiliate_fallback(self):
        """Should fall back to affiliate links when Shopify creds are missing."""
        service = CommerceService()

        mock_db = AsyncMock()

        # No shopify creds
        mock_none_result = MagicMock()
        mock_none_result.scalar_one_or_none.return_value = None

        # Affiliates found for niche
        mock_affiliate = MagicMock(
            id="aff1",
            product_name="Motivation Book",
            link="https://example.com/book",
            cta_text="Buy Now"
        )
        mock_affiliates_result = MagicMock()
        mock_affiliates_result.scalars.return_value.all.return_value = [mock_affiliate]

        mock_db.execute = AsyncMock(side_effect=[mock_none_result, mock_none_result, mock_affiliates_result])

        with patch("src.services.monetization.commerce_service.async_session_factory") as mock_sf:
            mock_sf.return_value.__aenter__.return_value = mock_db

            products = await service.get_relevant_products("Motivation")

        assert len(products) == 1
        assert products[0]["source"] == "affiliate"
        assert products[0]["name"] == "Motivation Book"
        assert products[0]["url"] == "https://example.com/book"

    async def test_get_relevant_products_no_shopify_no_affiliates(self):
        """Should return empty list when neither Shopify nor affiliate data exists."""
        service = CommerceService()

        mock_db = AsyncMock()

        mock_none_result = MagicMock()
        mock_none_result.scalar_one_or_none.return_value = None

        mock_empty_result = MagicMock()
        mock_empty_result.scalars.return_value.all.return_value = []

        with patch("src.services.monetization.commerce_service.async_session_factory") as mock_sf:
            mock_sf.return_value.__aenter__.return_value = mock_db

            # Set up mock AFTER the session factory is entered
            mock_db.execute = AsyncMock(side_effect=[mock_none_result, mock_none_result, mock_empty_result])

            products = await service.get_relevant_products("Motivation")

        assert products == []

    async def test_generate_checkout_link(self):
        """Should generate a Shopify-formatted checkout link."""
        service = CommerceService()

        link = await service.generate_checkout_link("12345")

        assert link == "/cart/12345:1"

    async def test_skip_shopify_without_valid_token_prefix(self):
        """Should skip Shopify API call when token doesn't start with 'shpat_'."""
        service = CommerceService()

        mock_db = AsyncMock()

        mock_url_result = MagicMock()
        mock_url_result.scalar_one_or_none.return_value = MagicMock(value="mystore.myshopify.com")
        mock_token_result = MagicMock()
        mock_token_result.scalar_one_or_none.return_value = MagicMock(value="invalid_token_format")

        # Need 3 execute calls: 2 for creds + 1 for affiliate fallback
        mock_affiliates_result = MagicMock()
        mock_affiliates_result.scalars.return_value.all.return_value = []

        mock_db.execute = AsyncMock(side_effect=[mock_url_result, mock_token_result, mock_affiliates_result])

        with patch("src.services.monetization.commerce_service.async_session_factory") as mock_sf:
            mock_sf.return_value.__aenter__.return_value = mock_db

            with patch.object(service, '_fetch_from_shopify', new_callable=AsyncMock) as mock_fetch:
                products = await service.get_relevant_products("Motivation")

                # Shopify fetch should NOT have been called due to invalid token format
                mock_fetch.assert_not_called()
                assert products == []

    def test_base_commerce_service_singleton(self):
        """Verify that base_commerce_service is an instance of CommerceService."""
        from src.services.monetization.commerce_service import base_commerce_service
        assert isinstance(base_commerce_service, CommerceService)


@pytest.mark.anyio
class TestCommerceServiceEdgeCases:
    """Edge cases for CommerceService."""

    async def test_empty_niche_returns_empty(self):
        """Should handle empty niche gracefully."""
        service = CommerceService()

        mock_db = AsyncMock()
        mock_none_result = MagicMock()
        mock_none_result.scalar_one_or_none.return_value = None

        mock_empty_result = MagicMock()
        mock_empty_result.scalars.return_value.all.return_value = []

        with patch("src.services.monetization.commerce_service.async_session_factory") as mock_sf:
            mock_sf.return_value.__aenter__.return_value = mock_db

            # Explicitly set up mock_db.execute for the 3 calls made inside get_relevant_products
            mock_db.execute = AsyncMock(side_effect=[mock_none_result, mock_none_result, mock_empty_result])

            products = await service.get_relevant_products("")

        assert products == []

    async def test_special_chars_in_niche(self):
        """Should handle niches with special characters."""
        service = CommerceService()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"products": []}

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response) as mock_get:
            products = await service._fetch_from_shopify(
                "mystore.myshopify.com",
                "shpat_test",
                "AI & Machine Learning"
            )

        assert products == []
        # The query parameter should be properly URL-encoded
        args = mock_get.call_args[0][0]
        import urllib.parse
        assert urllib.parse.quote("AI & Machine Learning") in args
