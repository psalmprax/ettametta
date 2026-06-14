"""
Remote Dify Script Generation E2E Test
Tests that Dify is reachable and that ScriptGenerator produces a valid script via Dify.
"""
import asyncio
import json
import sys
import os
import logging

sys.path.insert(0, "/app")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger("DifyScriptGenTest")

async def main():
    logger.info("=" * 60)
    logger.info("🚀 Starting Dify Script Generation E2E Test")
    logger.info("=" * 60)

    # Step 1: Verify Dify connectivity via IntelligenceHub
    logger.info("\n📡 Step 1: Testing Dify connectivity...")
    from src.services.llm.intelligence_hub import base_intelligence_service

    try:
        res = await base_intelligence_service.chat(
            prompt="Say 'DIFY_CONNECTED' if you can read this. Reply with only that phrase.",
            provider="dify",
            timeout_seconds=60
        )
        response = res.get("response", "")
        logger.info(f"✅ Dify responded: {response[:100]}")
        print(f"STEP1: DIFY_CONNECTED | response={response[:100]}")
    except Exception as e:
        logger.error(f"❌ Dify connectivity test failed: {e}")
        print(f"STEP1: FAILED | error={e}")
        # Continue anyway to test fallback

    # Step 2: Test ScriptGenerator with Dify (the newly wired provider)
    logger.info("\n📝 Step 2: Testing ScriptGenerator with Dify...")
    from src.services.script_generator.service import base_script_service

    try:
        script = await base_script_service.generate_script(
            topic="The Future of AI in Content Creation",
            niche="Tech",
            duration_sec=30,
            style="story",
            session_id="dify_e2e_test"
        )

        title = script.get("title", "N/A")
        segments = script.get("segments", [])
        hashtags = script.get("hashtags", [])

        logger.info(f"✅ Script generated via Dify!")
        logger.info(f"   Title: {title}")
        logger.info(f"   Segments: {len(segments)}")
        logger.info(f"   Hashtags: {hashtags}")

        # Validate the script structure
        is_valid = (
            len(segments) >= 2
            and all(s.get("text") for s in segments)
            and len(hashtags) >= 1
        )

        print(f"STEP2: {'VALID' if is_valid else 'INVALID'} | title={title} | segments={len(segments)} | hashtags={len(hashtags)}")

        if is_valid:
            # Print first segment as a sample
            first = segments[0]
            logger.info(f"   Sample segment: [{first.get('type')}] {first.get('text', '')[:80]}...")
        else:
            logger.warning(f"⚠️ Script validation failed — structure may be incomplete")
            logger.info(f"   Raw script: {json.dumps(script, indent=2)[:500]}")

    except Exception as e:
        logger.error(f"❌ ScriptGenerator via Dify failed: {e}")
        import traceback
        traceback.print_exc()
        print(f"STEP2: FAILED | error={e}")

    # Step 3: Quick DifyClient direct test (bypass IntelligenceHub)
    logger.info("\n🔧 Step 3: Direct DifyClient test...")
    from src.services.llm.dify_client import base_dify_client

    try:
        direct = await base_dify_client.chat_messages(
            query="Reply with exactly: DIRECT_DIFY_OK",
            user_id="ettametta_test",
            inputs={}
        )
        answer = direct.get("answer", "")
        logger.info(f"✅ Direct DifyClient: {answer[:100]}")
        print(f"STEP3: CONNECTED | answer={answer[:100]}")
    except Exception as e:
        logger.error(f"❌ Direct DifyClient test failed: {e}")
        print(f"STEP3: FAILED | error={e}")

    logger.info("\n" + "=" * 60)
    logger.info("🏁 Dify Script Generation E2E Test Complete")
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
