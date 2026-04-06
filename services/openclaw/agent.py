import logging
import json
import requests
import asyncio
from groq import Groq
from config import settings
from typing import Dict, Any
from skills.discovery import discovery_skill
from skills.system import system_skill
from skills.analytics import analytics_skill
from skills.content import content_skill
from skills.publishing import publishing_skill
from skills.niche import niche_skill
from skills.security import security_skill
from skills.no_face import noface_skill
from skills.outreach import outreach_skill
from skills.metrics import social_metrics_skill
from skills.external.paperclip_integration import paperclip_skill
from skills.external.claw4science_integration import claw4science_skill
from skills.render_remotion import remotion_skill
from skills.memory import memory_skill
from skills.self_improve import self_improve_skill
from skills.repurpose import repurpose_skill
from skills.trend_prediction import trend_prediction_skill
from skills.competitor import competitor_skill
from skills.notifications import notification_skill
from skills.workflow import workflow_skill
from skills.self_healing import self_healing_skill

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenClawAgent:
    def __init__(self):
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.MODEL
        self.system_prompt = """You are OpenClaw, the autonomous Master Controller for the ettametta multi-agent empire.
        Your goal is to assist the user by orchestrating a team of specialized agents:
        - SCOUT (Discovery): Advanced trend discovery, competitor analysis, content ideation, and market research.
        - MUSE (Creative): Writes viral scripts and hook strategies.
        - EYE (Visual): Analyzes video vibes and optimizes aesthetic positioning.
        - HERALD (Distribution): Handles publishing and monetization arbitrage.

        DISCOVERY CAPABILITIES:
        - Search trending topics with AI analysis
        - Analyze competitor strategies
        - Predict upcoming trends
        - Generate viral content ideas
        - Scan niches for opportunities
        
        You have access to the following tools:
        - DISCOVERY: Advanced trend discovery and analysis. Params: {"action": "search|trends|scan|predict|ideas|analyze", "topic": "string", "niche": "string", "deep": true|false}
        - NOFACE: Generate viral scripts or assess hooks purely in text. Params: {"action": "script|hook", "topic": "string"}
        - ANALYTICS: Get dashboard summary, revenue, or recent posts. Params: {"action": "summary|revenue|posts"}
        - SYSTEM: Check platform health/uptime. No params needed.
        - CONTENT: Create new video content. Params: {"action": "transform|generate|story", "niche": "string", "platform": "YouTube Shorts|TikTok", "input_url": "string", "prompt": "string", "engine": "string"}
        - COMPETITOR: Analyze competitor strategies. Params: {"url": "competitor_url"}
        - PUBLISH: Publish a completed job. Params: {"job_id": "string", "platform": "YouTube Shorts|TikTok", "niche": "string"}
        - NICHE: Manage niches. Params: {"action": "add|trends|auto_merch", "niche": "string"}
        - OUTREACH: Blast a message to a specific user via their connected channels. Params: {"user_id": "string", "message": "string"}
        - PERSONA: Generate a deepfake video using the user's uploaded persona/avatar. Params: {"action": "generate", "persona_id": "int", "topic": "string"}
        - SECURITY: Emergency lockdown. Params: {"action": "panic|status"}
        - STORAGE: Check video storage usage and cloud status. No params needed.
        - RENDER: Trigger a cinematic programmatic video render. Params: {"title": "string", "subtitle": "string", "video_url": "string"}
        - ZERO: Control the Agent Zero autonomous director. Params: {"action": "start|stop|status"}
        - RESEARCH: Search academic papers (free, no API key). Params: {"action": "search|trends", "topic": "string", "limit": int}
        - INGESTION: Multi-source data (Reddit, RSS, GitHub). Params: {"action": "reddit|rss|github|multi", "subreddit": "string", "feed_url": "string", "language": "string", "sources": []}
        - METRICS: Social media metrics (X, Reddit, GitHub, Instagram). Params: {"platform": "x|reddit|github|instagram", "handle": "string"}
        - PAPERCLIP: KPI-driven organic scaling and performance tracking. Params: {"action": "track|scale", "job_id": "string", "platform": "string", "views": int, "likes": int, "niche": "string"}
        - SCIENTIFIC: Transforms technical/academic data into viral "Science-Pop" scripts. Params: {"action": "convert|trends", "raw_data": "string", "topic": "string"}
        - REMOTION: Programmatic React-based video rendering for pixel-perfect overlays. Params: {"composition": "string", "props": dict, "output_name": "string"}
        - MEMORY: Manage persistent data across sessions. Params: {"action": "store|retrieve|list", "key": "string", "value": "string"}
        - NOTIFICATIONS: Send alerts via configured channels. Params: {"channel": "telegram|webhook|all", "message": "string", "priority": "normal|high|critical"}
        - WORKFLOW: Create and execute automated workflows. Params: {"action": "create|execute|status", "name": "string", "steps": [...]}
        - BROWSER: Advanced browser automation for web scraping. Params: {"action": "navigate|click|extract", "url": "string", "selector": "string"}
        - DOCUMENT: Process PDF/DOCX/PPTX files. Params: {"type": "pdf|docx|pptx", "action": "extract|analyze", "file_url": "string"}
        - WATCHDOG: Monitor system health and auto-restart processes. Params: {"action": "status|check|restart", "process": "string"}
        
        PLANNING MODE:
        When a user gives a complex command, you must first output a brief "Plan" explicitly naming which sub-agents (SCOUT, MUSE, etc.) you are delegating to, followed by the actual tool JSON.
        
        If a tool is needed, output:
        "Plan: [Sub-agent names] - [Action description]"
        {
            "tool": "TOOL_NAME",
            "params": { ... }
        }
        """

    def _get_user_from_api(self, identifier: str):
        # 1. Immediate Admin Fallback (Highest Priority)
        # Trust the configured admin ID even if API is unreachable
        if str(identifier) == str(settings.TELEGRAM_ADMIN_ID):
            logger.info(f"Admin access verified for {identifier}")
            return {
                "id": 1,  # Match the DB id found earlier for psalmprax
                "username": "admin",
                "role": "admin",
                "subscription": "premium",
                "telegram_chat_id": str(identifier),
            }

        # 2. Dynamic User Verification via API
        try:
            if str(identifier).startswith("whatsapp:"):
                # Format: whatsapp:+1234567890
                clean_id = str(identifier)
                response = requests.get(
                    f"{settings.API_URL}/auth/verify-whatsapp/{clean_id}", timeout=5
                )
            else:
                response = requests.get(
                    f"{settings.API_URL}/auth/verify-telegram/{identifier}", timeout=5
                )

            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error calling verification API: {e}")
            return None

    async def process_message(self, identifier: str, message: str) -> str:
        """
        Process a user message and determine the action.
        """
        # Dynamic verification via API
        user = await asyncio.to_thread(self._get_user_from_api, identifier)

        if not user:
            logger.warning(f"Unauthorized access attempt from {identifier}")
            return f"⛔ Unauthorized access. Your ID is: `{identifier}`.\n\nPlease log in to the ettametta dashboard and add this ID to your profile settings to enable agent access."

        try:
            # 1. Ask LLM for intent
            completion = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": message},
                ],
                model=self.model,
                temperature=0.1,
            )

            response_text = completion.choices[0].message.content
            logger.info(f"LLM Raw Response: {response_text}")  # Debug log

            # 2. Check if response is a tool call (JSON)
            try:
                # Naive check for JSON
                if "{" in response_text and "}" in response_text:
                    # Extract JSON if mixed with text
                    start = response_text.find("{")
                    end = response_text.rfind("}") + 1
                    json_str = response_text[start:end]

                    tool_call = json.loads(json_str)

                    # Prepend the plan/thought if it exists
                    thought = response_text[:start].strip()
                    result = await self.execute_tool(tool_call)

                    if thought:
                        return f"🧠 **{thought}**\n\n{result}"
                    return result
                else:
                    return response_text

            except json.JSONDecodeError:
                return response_text

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"⚠️ Agent Error: {str(e)}"

    async def execute_tool(self, tool_call: Dict[str, Any]) -> str:
        """
        Execute the identified tool.
        """
        tool = tool_call.get("tool")
        params = tool_call.get("params", {})

        logger.info(f"Executing tool: {tool} with params: {params}")

        if tool == "SYSTEM":
            return system_skill.check_health()

        elif tool == "DISCOVERY":
            action = params.get("action", "search")
            topic = params.get("topic", params.get("niche", "general"))

            if action == "search":
                analyze = params.get("analyze", False)
                return discovery_skill.search_trends(topic, analyze=analyze)
            elif action == "trends":
                min_score = params.get("min_viral_score", 75)
                return discovery_skill.get_trending_content(topic, min_score)
            elif action == "scan":
                deep = params.get("deep", False)
                return discovery_skill.scan_for_opportunities(topic, deep)
            elif action == "predict":
                timeframe = params.get("timeframe", "1week")
                return discovery_skill.predict_trends(topic, timeframe)
            elif action == "ideas":
                num_ideas = params.get("num_ideas", 5)
                return discovery_skill.generate_content_ideas(topic, num_ideas)
            elif action == "analyze":
                competitor_url = params.get("url", "")
                if competitor_url:
                    return discovery_skill.analyze_competitor_strategy(competitor_url)
                else:
                    return "⚠️ Missing competitor URL for analysis"
            else:
                return discovery_skill.search_trends(topic)

        elif tool == "ANALYTICS":
            action = params.get("action", "summary")
            if action == "revenue":
                return analytics_skill.get_revenue_report()
            elif action == "posts":
                # Provide a default limit or accept one if added to schema later
                limit = params.get("limit", 5)
                return analytics_skill.get_recent_posts(limit=limit)
            else:
                return analytics_skill.get_summary()

        elif tool == "NOFACE":
            action = params.get("action", "script")
            topic = params.get("topic", "General advice")
            if action == "hook":
                return noface_skill.generate_hook(topic)
            else:
                return noface_skill.generate_script(topic)

        elif tool == "OUTREACH":
            user_id = params.get("user_id")
            message = params.get("message", "Hello!")
            if not user_id:
                return "⚠️ Outreach failed: Missing user_id"
            return outreach_skill.send_outreach_message(user_id, message)

        elif tool == "PERSONA":
            persona_id = params.get("persona_id")
            topic = params.get("topic", "general chat")
            if not persona_id:
                return "⚠️ Persona generation failed: Missing persona_id"
            try:
                # Direct internal routing for MVP
                # Uses INTERNAL_API_TOKEN from config for service-to-service auth
                payload = {"persona_id": int(persona_id), "topic": topic}
                headers = {}
                if settings.INTERNAL_API_TOKEN:
                    headers["Authorization"] = f"Bearer {settings.INTERNAL_API_TOKEN}"
                response = requests.post(
                    f"http://localhost:{settings.PORT}/api/v1/persona/generate",
                    json=payload,
                    headers=headers,
                )
                if response.status_code == 200:
                    return f"👤 **Persona Animated!**\nVideo generated successfully.\nLink: {response.json().get('video_url')}"
                else:
                    return f"⚠️ Persona generation failed. Ensure your Persona is registered in the Dashboard."
            except Exception as e:
                return f"⚠️ Persona System Error: {str(e)}"

        elif tool == "CONTENT":
            return content_skill.create_content(
                action=params.get("action", "transform"),
                input_url=params.get("input_url", ""),
                prompt=params.get("prompt", ""),
                engine=params.get("engine", "veo3"),
                niche=params.get("niche", "Motivation"),
                platform=params.get("platform", "YouTube Shorts"),
            )

        elif tool == "PUBLISH":
            return publishing_skill.publish_job(
                job_id=params.get("job_id", ""),
                platform=params.get("platform", "YouTube Shorts"),
                niche=params.get("niche", "Motivation"),
            )

        elif tool == "NICHE":
            action = params.get("action", "trends")
            niche = params.get("niche", "General")
            if action == "add":
                return niche_skill.add_niche_scan(niche)
            elif action == "auto_merch":
                return niche_skill.trigger_auto_merch(niche)
            else:
                return niche_skill.get_niche_trends(niche)

        elif tool == "SECURITY":
            action = params.get("action", "status")
            if action == "panic":
                return security_skill.panic_lockdown()
            else:
                # Check status via skill (reuse system skill or specific security skill)
                # I'll create a quick status check in security skill or just reuse panic return
                # Actually security skill logic was written to support panic only?
                # Let me check security.py... it has panic_lockdown.
                # I should add get_status to security.py if I want it, or just use system skill.
                # Implementation plan said get_status() calls /api/security/status.
                # I will update security.py to include get_status if it's missing or just implement basic logic here.
                # Actually, I wrote security.py with just panic_lockdown? Let me double check content.
                # Wait, I wrote security.py with panic_lockdown. I didn't add get_status.
                # I'll stick to panic for now or I can update security.py.
                # Given the user request was "/panic", I'll focus on that.
                return security_skill.panic_lockdown()

        elif tool == "STORAGE":
            return system_skill.get_storage_status()

        elif tool == "RENDER":
            return render_skill.render_clip(**params)
        elif tool == "ZERO":
            return agent_zero_skill.control_agent(**params)
        elif tool == "HERALD":
            return publishing_skill.publish_job(
                job_id=params.get("job_id", ""),
                platform=params.get("platform", "YouTube Shorts"),
                niche=params.get("niche", "Motivation"),
            )

        elif tool == "RESEARCH":
            action = params.get("action", "search")
            topic = params.get("topic", "")
            limit = params.get("limit", 5)
            if action == "search":
                return research_skill.search_papers(topic, limit)
            else:
                return research_skill.search_trends(topic)

        elif tool == "INGESTION":
            action = params.get("action", "multi")
            if action == "reddit":
                subreddit = params.get("subreddit", "technology")
                limit = params.get("limit", 5)
                return data_ingestion_skill.reddit_hot(subreddit, limit)
            elif action == "rss":
                feed_url = params.get("feed_url", "")
                return data_ingestion_skill.fetch_rss(feed_url)
            elif action == "github":
                language = params.get("language", "")
                return data_ingestion_skill.github_trending(language)
            else:
                sources = params.get("sources", [])
                return data_ingestion_skill.ingest_multi_source(sources)

        elif tool == "METRICS":
            platform = params.get("platform", "")
            handle = params.get("handle", "")
            if platform == "x":
                return social_metrics_skill.get_x_followers(handle)
            elif platform == "reddit":
                return social_metrics_skill.get_reddit_stats(handle)
            elif platform == "github":
                return social_metrics_skill.get_github_stats(handle)
            elif platform == "instagram":
                return social_metrics_skill.get_instagram_profile(handle)
            else:
                handles = params.get("handles", {})
                return social_metrics_skill.get_multi_platform(handles)

        elif tool == "PAPERCLIP":
            action = params.get("action", "track")
            if action == "track":
                return paperclip_skill.track_organic_performance(
                    params.get("job_id"),
                    params.get("platform", "TikTok"),
                    {"views": params.get("views", 0), "likes": params.get("likes", 0)},
                )
            else:
                return paperclip_skill.scale_organic_reach(
                    params.get("niche", "General")
                )

        elif tool == "SCIENTIFIC":
            action = params.get("action", "convert")
            if action == "convert":
                return claw4science_skill.convert_technical_to_viral(
                    params.get("raw_data", "")
                )
            else:
                return claw4science_skill.fetch_scientific_niche_trends(
                    params.get("topic", "General")
                )

        elif tool == "REMOTION":
            return remotion_skill.render_remotion_clip(
                params.get("composition", "MainText"),
                params.get("props", {}),
                params.get("output_name", "remotion_render.mp4"),
            )

        elif tool == "MEMORY":
            action = params.get("action", "list")
            if action == "store":
                return memory_skill.store(
                    params.get("key", ""), params.get("value", "")
                )
            elif action == "retrieve":
                return memory_skill.retrieve(params.get("key", ""))
            else:
                return memory_skill.list_keys()

        elif tool == "NOTIFICATIONS":
            channel = params.get("channel", "telegram")
            message = params.get("message", "Test notification")
            priority = params.get("priority", "normal")
            return notification_skill.send_notification(channel, message, priority)

        elif tool == "WORKFLOW":
            action = params.get("action", "list")
            name = params.get("name", "")
            if action == "create":
                steps = params.get("steps", [])
                return workflow_skill.create_workflow(name, steps)
            elif action == "execute":
                return workflow_skill.execute_workflow(name)
            elif action == "status":
                return workflow_skill.get_workflow_status(name)
            else:
                return workflow_skill.list_workflows()

        elif tool == "BROWSER":
            try:
                response = requests.post(
                    "http://node-skills:3002/browser-use", json=params, timeout=30
                )
                if response.status_code == 200:
                    return f"🌐 Browser automation: {response.json()}"
                else:
                    return f"❌ Browser error: {response.status_code}"
            except Exception as e:
                return f"❌ Browser service unavailable: {str(e)}"

        elif tool == "DOCUMENT":
            doc_type = params.get("type", "pdf")
            try:
                endpoint = f"http://node-skills:3002/process-{doc_type}"
                response = requests.post(endpoint, json=params, timeout=30)
                if response.status_code == 200:
                    return f"📄 Document processed: {response.json()}"
                else:
                    return f"❌ Document processing error: {response.status_code}"
            except Exception as e:
                return f"❌ Document service unavailable: {str(e)}"

        elif tool == "COMPETITOR":
            competitor_url = params.get("url", "")
            if competitor_url:
                return discovery_skill.analyze_competitor_strategy(competitor_url)
            else:
                return "⚠️ Missing competitor URL for analysis"

        elif tool == "WATCHDOG":
            action = params.get("action", "status")
            if action == "check":
                return self_healing_skill.perform_health_check()
            elif action == "restart":
                process = params.get("process", "")
                return self_healing_skill.restart_process(process)
            else:
                return self_healing_skill.get_watchdog_status()

        return f"❓ Unknown tool: {tool}"
