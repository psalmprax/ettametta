"""
Revenue Engine CLI — Command-line interface for the revenue automation system.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def cmd_research(args):
    """Research a niche."""
    from src.services.revenue_engine.orchestrator import RevenueEngine
    engine = RevenueEngine(scraper_url=args.scraper_url, etsy_api_key=args.etsy_key)
    result = await engine.quick_test(args.niche)
    print(json.dumps(result, indent=2))
    await engine.close()


async def cmd_research_etsy(args):
    """Research Etsy using API and Google proxy."""
    from src.services.revenue_engine.orchestrator import RevenueEngine
    engine = RevenueEngine(scraper_url=args.scraper_url, etsy_api_key=args.etsy_key)
    result = await engine.research_etsy(args.niche)
    print(json.dumps(result, indent=2, default=str))
    await engine.close()


async def cmd_research_pinterest(args):
    """Research Pinterest for visual product intelligence."""
    from src.services.revenue_engine.orchestrator import RevenueEngine
    engine = RevenueEngine(scraper_url=args.scraper_url)
    result = await engine.research_pinterest(args.niche)
    print(json.dumps(result, indent=2, default=str))
    await engine.close()


async def cmd_run(args):
    """Run full pipeline."""
    from src.services.revenue_engine.orchestrator import RevenueEngine
    engine = RevenueEngine(scraper_url=args.scraper_url)
    niches = args.niches.split(",")
    result = await engine.run_pipeline(
        niches=niches,
        auto_traffic=not args.no_traffic,
    )
    print(json.dumps(result.results, indent=2))
    await engine.close()


async def cmd_analyze(args):
    """Analyze performance and get recommendations."""
    from src.services.revenue_engine.orchestrator import RevenueEngine
    engine = RevenueEngine()
    report = engine.monitor.generate_report()
    recommendations = engine.get_optimization_recommendations()
    print("=== Performance Report ===")
    print(json.dumps(report, indent=2))
    print("\n=== Recommendations ===")
    for rec in recommendations:
        print(f"  - {rec}")
    await engine.close()


def main():
    parser = argparse.ArgumentParser(description="Revenue Engine CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Research command
    research_parser = subparsers.add_parser("research", help="Research a niche")
    research_parser.add_argument("niche", help="Niche to research")
    research_parser.add_argument("--scraper-url", default="http://localhost:8010")
    research_parser.add_argument("--etsy-key", default="", help="Etsy API key")

    # Etsy research command
    etsy_parser = subparsers.add_parser("etsy", help="Research Etsy via API + Google")
    etsy_parser.add_argument("niche", help="Niche to research")
    etsy_parser.add_argument("--scraper-url", default="http://localhost:8010")
    etsy_parser.add_argument("--etsy-key", default="", help="Etsy API key")

    # Pinterest research command
    pin_parser = subparsers.add_parser("pinterest", help="Research Pinterest for visual products")
    pin_parser.add_argument("niche", help="Niche to research")
    pin_parser.add_argument("--scraper-url", default="http://localhost:8010")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run full pipeline")
    run_parser.add_argument("niches", help="Comma-separated niches")
    run_parser.add_argument("--no-traffic", action="store_true", help="Skip traffic generation")
    run_parser.add_argument("--scraper-url", default="http://localhost:8010")
    run_parser.add_argument("--etsy-key", default="", help="Etsy API key")

    # Analyze command
    subparsers.add_parser("analyze", help="Analyze performance")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "research":
        asyncio.run(cmd_research(args))
    elif args.command == "etsy":
        asyncio.run(cmd_research_etsy(args))
    elif args.command == "pinterest":
        asyncio.run(cmd_research_pinterest(args))
    elif args.command == "run":
        asyncio.run(cmd_run(args))
    elif args.command == "analyze":
        asyncio.run(cmd_analyze(args))


if __name__ == "__main__":
    main()
