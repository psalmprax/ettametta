"""
Revenue Engine API — FastAPI endpoints for the revenue automation system.
"""

from fastapi import FastAPI, Query

app = FastAPI(title="Revenue Engine", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "revenue-engine"}


@app.post("/research")
async def research_niche(niche: str, scraper_url: str = "http://cloakbrowser:8010"):
    """Research a niche on Etsy."""
    from .orchestrator import RevenueEngine
    engine = RevenueEngine(scraper_url=scraper_url)
    result = await engine.quick_test(niche)
    await engine.close()
    return result


@app.post("/research/etsy")
async def research_etsy(
    niche: str,
    etsy_api_key: str = "",
    scraper_url: str = "http://cloakbrowser:8010",
):
    """Research Etsy using API + Google proxy."""
    from .orchestrator import RevenueEngine
    engine = RevenueEngine(scraper_url=scraper_url, etsy_api_key=etsy_api_key)
    result = await engine.research_etsy(niche)
    await engine.close()
    return result


@app.post("/research/pinterest")
async def research_pinterest(
    niche: str,
    scraper_url: str = "http://cloakbrowser:8010",
):
    """Research Pinterest for visual product intelligence."""
    from .orchestrator import RevenueEngine
    engine = RevenueEngine(scraper_url=scraper_url)
    result = await engine.research_pinterest(niche)
    await engine.close()
    return result


@app.post("/pipeline")
async def run_pipeline(
    niches: str = Query(..., description="Comma-separated niches"),
    auto_traffic: bool = Query(True, description="Generate traffic content"),
    scraper_url: str = "http://cloakbrowser:8010",
):
    """Run the full revenue pipeline."""
    from .orchestrator import RevenueEngine
    engine = RevenueEngine(scraper_url=scraper_url)
    niche_list = [n.strip() for n in niches.split(",")]
    result = await engine.run_pipeline(niches=niche_list, auto_traffic=auto_traffic)
    await engine.close()
    return {
        "run_id": result.run_id,
        "status": result.status,
        "products_created": result.products_created,
        "listings_optimized": result.listings_optimized,
        "posts_generated": result.posts_generated,
        "results": result.results,
    }


@app.get("/analyze")
async def analyze_performance():
    """Get performance analysis and recommendations."""
    from .orchestrator import RevenueEngine
    engine = RevenueEngine()
    report = engine.monitor.generate_report()
    recommendations = engine.get_optimization_recommendations()
    await engine.close()
    return {"report": report, "recommendations": recommendations}


@app.get("/recommendations")
async def get_recommendations():
    """Get self-optimization recommendations."""
    from .orchestrator import RevenueEngine
    engine = RevenueEngine()
    recommendations = engine.get_optimization_recommendations()
    await engine.close()
    return {"recommendations": recommendations}
