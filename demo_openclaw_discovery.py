#!/usr/bin/env python3
"""
OpenClaw Discovery Demo

Demonstrates how OpenClaw agents can now handle advanced discovery tasks
using the enhanced discovery skill.
"""

import asyncio
from services.openclaw.agent import OpenClawAgent


async def demo_openclaw_discovery():
    """Demo OpenClaw's enhanced discovery capabilities"""

    agent = OpenClawAgent()

    print("🤖 OpenClaw Discovery Demo")
    print("=" * 50)

    # Test different discovery actions
    discovery_tasks = [
        {
            "tool": "DISCOVERY",
            "params": {"action": "search", "topic": "AI productivity tools"},
        },
        {
            "tool": "DISCOVERY",
            "params": {
                "action": "trends",
                "niche": "Motivation",
                "min_viral_score": 80,
            },
        },
        {
            "tool": "DISCOVERY",
            "params": {"action": "predict", "niche": "Tech", "timeframe": "1week"},
        },
        {
            "tool": "DISCOVERY",
            "params": {"action": "ideas", "niche": "Fitness", "num_ideas": 3},
        },
        {
            "tool": "DISCOVERY",
            "params": {"action": "scan", "niche": "Crypto", "deep": False},
        },
    ]

    for i, task in enumerate(discovery_tasks, 1):
        print(f"\n🔍 Discovery Task {i}: {task['params']['action'].upper()}")
        print("-" * 30)

        try:
            result = await agent.execute_tool(task)
            print(result[:500] + "..." if len(result) > 500 else result)
        except Exception as e:
            print(f"❌ Error: {e}")

        print()


if __name__ == "__main__":
    asyncio.run(demo_openclaw_discovery())
