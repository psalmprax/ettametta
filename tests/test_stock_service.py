import pytest
from src.services.video_engine.stock_service import base_stock_service, StockService


def test_stock_service_product_prompt_optimization():
    service = StockService()

    opt_tech = service.optimize_product_broll_prompt("laptop app")
    assert "cinematic studio macro product shot" in opt_tech
    assert "glass reflection" in opt_tech

    opt_fashion = service.optimize_product_broll_prompt("leather sneaker")
    assert "slow motion turn table" in opt_fashion

    opt_food = service.optimize_product_broll_prompt("iced coffee")
    assert "high speed camera" in opt_food


def test_stock_service_search_keywords():
    service = StockService()
    keywords = service._get_search_keywords("wireless earbuds")
    assert len(keywords) >= 2
    assert "earbuds" in keywords[0] or "earbuds" in keywords[1]
