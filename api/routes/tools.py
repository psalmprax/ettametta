from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
)

from services.openclaw.skills.external import (
    popular_skills,
    clawhub_loader,
    langchain_service,
    prompt_manager,
    crewai_service,
    viralforge_crew,
    trading_service,
    market_analysis,
    interpreter_service,
    blog_seo_service,
    tradingview_service,
    backtest_service,
    metatrader_service,
    binance_service,
)
from services.openclaw.skills.research import ResearchSkill
from services.openclaw.skills.content import ContentSkill
from services.openclaw.skills.analytics import AnalyticsSkill

social_metrics_skill = AnalyticsSkill()

router = APIRouter(prefix="/tools", tags=["Tools & Skills"])


class ResearchRequest(BaseModel):
    query: str
    limit: int = 5


class IngestionRequest(BaseModel):
    action: str
    subreddit: Optional[str] = None
    feed_url: Optional[str] = None
    language: Optional[str] = None
    sources: Optional[List[str]] = None


class MetricsRequest(BaseModel):
    platform: str
    handle: str


class ClawHubSearchRequest(BaseModel):
    query: str
    category: Optional[str] = None


class PromptTemplateRequest(BaseModel):
    template: str
    variables: Optional[Dict[str, str]] = None


class TradingRequest(BaseModel):
    action: str
    symbol: Optional[str] = None
    coin_id: Optional[str] = None


class CrewRequest(BaseModel):
    crew_type: str
    topic: str


@router.post("/research")
async def search_academic_papers(request: ResearchRequest):
    """Search academic papers via OpenAlex API (free, no API key)"""
    return {"result": research_skill.search_papers(request.query, request.limit)}


@router.post("/ingestion")
async def ingest_data(request: IngestionRequest):
    """Multi-source data ingestion (Reddit, RSS, GitHub)"""
    action = request.action

    if action == "reddit":
        return {
            "result": data_ingestion_skill.reddit_hot(
                request.subreddit or "technology", 5
            )
        }
    elif action == "rss":
        return {"result": data_ingestion_skill.fetch_rss(request.feed_url or "")}
    elif action == "github":
        return {"result": data_ingestion_skill.github_trending(request.language or "")}
    elif action == "multi":
        return {
            "result": data_ingestion_skill.ingest_multi_source(request.sources or [])
        }
    return {"error": f"Unknown action: {action}"}


@router.post("/metrics")
async def get_social_metrics(request: MetricsRequest):
    """Get social media metrics"""
    platform = request.platform
    handle = request.handle

    if platform == "x":
        return {"result": social_metrics_skill.get_x_followers(handle)}
    elif platform == "reddit":
        return {"result": social_metrics_skill.get_reddit_stats(handle)}
    elif platform == "github":
        return {"result": social_metrics_skill.get_github_stats(handle)}
    elif platform == "instagram":
        return {"result": social_metrics_skill.get_instagram_profile(handle)}
    return {"error": f"Unknown platform: {platform}"}


@router.get("/skills/popular")
async def get_popular_skills():
    """Get popular ClawHub skills relevant to viral_forge"""
    return {
        "skills": popular_skills.get_all_skills(),
        "high_priority": popular_skills.get_skills_by_priority("high"),
        "enabled": os.getenv("ENABLE_CREWAI", "false").lower() == "true",
    }


@router.post("/skills/search")
async def search_clawhub_skills(request: ClawHubSearchRequest):
    """Search skills from ClawHub GitHub repository"""
    results = clawhub_loader.search_skills(request.query, request.category)
    return {"results": results, "count": len(results)}


@router.get("/skills/categories")
async def get_skill_categories():
    """Get available skill categories from ClawHub"""
    categories = clawhub_loader.list_categories()
    return {"categories": categories}


@router.post("/prompt/template")
async def use_prompt_template(request: PromptTemplateRequest):
    """Use a predefined prompt template"""
    template = prompt_manager.get_template(request.template)
    if not template:
        return {"error": f"Template '{request.template}' not found"}

    variables = request.variables or {}
    rendered = prompt_manager.render_template(request.template, **variables)
    return {
        "template": request.template,
        "system": rendered["system"],
        "human": rendered["human"],
    }


@router.get("/prompt/templates")
async def list_prompt_templates():
    """List all available prompt templates"""
    return {"templates": prompt_manager.list_templates()}


@router.get("/langchain/status")
async def langchain_status():
    """Check LangChain integration status"""
    return {
        "enabled": langchain_service.enabled,
        "message": "LangChain integration active"
        if langchain_service.enabled
        else "Set ENABLE_LANGCHAIN=true to enable",
    }


@router.post("/crew/run")
async def run_crewai_crew(request: CrewRequest):
    """Run a CrewAI crew for content creation"""
    if request.crew_type == "content":
        result = await viralforge_crew.run_content_team(request.topic)
    elif request.crew_type == "affiliate":
        result = await viralforge_crew.run_affiliate_campaign(request.topic)
    else:
        return {"error": f"Unknown crew type: {request.crew_type}"}

    return {"result": result, "crew_type": request.crew_type}


@router.get("/crewai/status")
async def crewai_status():
    """Check CrewAI integration status"""
    return {
        "enabled": crewai_service.enabled,
        "message": "CrewAI integration active"
        if crewai_service.enabled
        else "Set ENABLE_CREWAI=true to enable",
    }


@router.post("/trading/quote")
async def get_trading_quote(request: TradingRequest):
    """Get stock or crypto quote"""
    action = request.action

    if action == "stock":
        return {"result": trading_service.get_stock_quote(request.symbol or "AAPL")}
    elif action == "crypto":
        return {
            "result": trading_service.get_crypto_price(request.coin_id or "bitcoin")
        }
    elif action == "top_coins":
        return {"result": trading_service.get_top_coins()}
    elif action == "sentiment":
        return {
            "result": trading_service.get_market_sentiment(request.symbol or "AAPL")
        }

    return {"error": f"Unknown action: {action}"}


@router.get("/trading/status")
async def trading_status():
    """Check trading API configuration status"""
    alpha_enabled = bool(os.getenv("ALPHA_VANTAGE_API_KEY"))
    coingecko_enabled = True  # CoinGecko has free tier

    return {
        "alpha_vantage": {
            "enabled": alpha_enabled,
            "message": "Alpha Vantage configured"
            if alpha_enabled
            else "Set ALPHA_VANTAGE_API_KEY for stock data",
        },
        "coingecko": {
            "enabled": coingecko_enabled,
            "message": "CoinGecko free tier available",
        },
    }


@router.get("/market/opportunities")
async def get_market_opportunities():
    """Get content opportunities based on market data"""
    return {"opportunities": market_analysis.get_content_opportunities()}


@router.get("/interpreter/status")
async def interpreter_status():
    """Check Open Interpreter status"""
    return {
        "enabled": interpreter_service.enabled,
        "message": "Open Interpreter active"
        if interpreter_service.enabled
        else "Set ENABLE_INTERPRETER=true to enable",
    }


@router.post("/interpreter/execute")
async def execute_code(request: dict):
    """Execute code in sandbox"""
    code = request.get("code", "")
    language = request.get("language", "python")
    timeout = request.get("timeout", 60)

    result = interpreter_service.execute_code(code, language, timeout)
    return result


@router.post("/seo/content")
async def generate_seo_content(request: dict):
    """Generate SEO-optimized blog content"""
    topic = request.get("topic", "")
    content_type = request.get("content_type", "blog")
    word_count = request.get("word_count", 500)

    result = blog_seo_service.generate_seo_content(topic, content_type, word_count)
    return result


@router.get("/tradingview/status")
async def tradingview_status():
    """Check TradingView integration status"""
    return await tradingview_service.get_market_overview()


class BacktestRequest(BaseModel):
    symbol: str = "AAPL"
    strategy: str = "simple_ma"
    start_date: str = "2025-01-01"
    end_date: str = "2025-12-31"


@router.post("/backtest/run")
async def run_backtest(request: BacktestRequest):
    """
    Run a backtest on historical data with real strategy implementation.
    Strategies: simple_ma, momentum, mean_reversion
    """
    result = await backtest_service.run_backtest(
        request.symbol, request.strategy, request.start_date, request.end_date
    )
    return result


@router.get("/metatrader/status")
async def metatrader_status():
    """Check MetaTrader status"""
    return {
        "enabled": metatrader_service.enabled,
        "message": "MetaTrader 5 connected"
        if metatrader_service.enabled
        else "Set ENABLE_META_TRADER=true and install MetaTrader5 package",
    }


@router.get("/metatrader/account")
async def get_mt_account():
    """Get MetaTrader account info"""
    return metatrader_service.get_account_info()


@router.get("/metatrader/symbols")
async def get_mt_symbols():
    """Get available MetaTrader symbols"""
    return {"symbols": metatrader_service.get_symbols()}


@router.get("/metatrader/positions")
async def get_mt_positions():
    """Get open MetaTrader positions"""
    return {"positions": metatrader_service.get_positions()}


@router.post("/binance/price")
async def get_binance_price(request: dict):
    """Get Binance price for symbol"""
    symbol = request.get("symbol", "BTCUSDT")
    return binance_service.get_ticker_price(symbol)


@router.get("/binance/klines")
async def get_binance_klines(
    symbol: str = "BTCUSDT", interval: str = "1h", limit: int = 100
):
    """Get Binance candlestick data"""
    return {"klines": binance_service.get_klines(symbol, interval, limit)}
