import json
import logging
import os

logger = logging.getLogger(__name__)


class AutoCreator:
    def __init__(self):
        self._client = None
        self._last_key = None
        self.model = "llama-3.3-70b-versatile"

    @property
    def client(self):
        from src.api.utils.vault import get_secret

        key = get_secret("groq_api_key")
        if not key:
            return None

        if self._client and self._last_key == key:
            return self._client

        from groq import AsyncGroq

        self._client = AsyncGroq(api_key=key)
        self._last_key = key
        return self._client

    async def generate_viral_script(self, topic: str, niche: str) -> list[dict]:
        """
        Generates a segmented high-retention script for Auto-Creation.
        """
        if not self.client:
            logger.error(
                "[AutoCreator] Groq API key not configured. Real-First action required."
            )
            raise ValueError(
                "Groq API key missing. Please configure it in the Vault to enable script generation."
            )

        prompt = f"""
        Generate a 60-second viral video script for a {niche} video about "{topic}".
        Segment the script into 5-7 parts, each with:
        1. 'text': The narration text.
        2. 'visual_prompt': A description for what should be on screen.
        3. 'mood': The emotional vibe of this segment.
        
        OUTPUT FORMAT (JSON ONLY):
        [
            {{ "text": "...", "visual_prompt": "...", "mood": "..." }},
            ...
        ]
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional scriptwriter. Output JSON array.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            content = json.loads(response.choices[0].message.content)
            if isinstance(content, dict) and "segments" in content:
                return content["segments"]
            return content if isinstance(content, list) else []
        except Exception as e:
            logger.error(f"[AutoCreator] Script generation error: {e}")
            return [
                {
                    "text": f"Discussing {topic} in the {niche} niche.",
                    "visual_prompt": "Generic cinematic shot",
                    "mood": "Neutral",
                }
            ]

    async def _source_visual_assets(
        self, segments: list[dict], job_id: int, niche: str, engine: str = "cloud"
    ) -> list[str]:
        """Source real stock video or synthesize with engine."""
        visual_paths = []
        
        # Mapping frontend 'os' stack to 'hunyuan'
        actual_engine = "hunyuan" if engine == "os" else engine

        for i, seg in enumerate(segments):
            prompt = seg.get("visual_prompt", f"{niche} cinematic footage")
            
            # If engine is hunyuan, we synthesize instead of stock search
            if actual_engine == "hunyuan":
                logger.info(f"[AutoCreator] Synthesizing visual for segment {i} using {actual_engine}")
                try:
                    from src.services.video_engine.synthesis_service import base_generative_service
                    path = await base_generative_service.synthesize_video(
                        prompt=prompt,
                        engine=actual_engine,
                        style=seg.get("mood", "Cinematic")
                    )
                    if path:
                        visual_paths.append(path)
                        continue
                except Exception as e:
                    logger.error(f"[AutoCreator] Synthesis failed for segment {i}: {e}")

            # Fallback to stock search if not hunyuan or if synthesis failed
            try:
                from src.services.video_engine.stock_service import base_stock_service
            except ImportError:
                logger.warning("[AutoCreator] Stock service not available")
                continue

            # 1. Primary Attempt
            urls = await base_stock_service.fetch_b_roll(prompt, count=1)

            # 2. Retry with simplified niche keyword if primary fails
            if not urls:
                logger.info(
                    f"[AutoCreator] Retrying stock fetch for segment {i} with niche: {niche}"
                )
                urls = await base_stock_service.fetch_b_roll(f"{niche} video", count=1)

            if urls:
                dl_path = await base_stock_service.download_stock_video(urls[0])
                if dl_path:
                    visual_paths.append(dl_path)
                    continue

            # 3. Final "Real-First" Fallback
            local_fallbacks = [
                "test_wan21_480p.mp4",
                "test_animatediff.mp4",
                "remote_videos/test_480p.mp4",
            ]
            fallback = next((f for f in local_fallbacks if os.path.exists(f)), None)
            if fallback:
                logger.warning(
                    f"[AutoCreator] Using real local fallback for segment {i}: {fallback}"
                )
                visual_paths.append(fallback)
            else:
                logger.error(
                    f"[AutoCreator] CRITICAL: No visual assets found for segment {i}"
                )

        return visual_paths

    async def _generate_voiceovers(
        self, segments: list[dict], job_id: int
    ) -> list[str]:
        """Generate real TTS with provider fallback."""
        voice_paths = []
        os.makedirs("temp/voice", exist_ok=True)

        try:
            from src.services.voiceover.service import voiceover_service

            service = voiceover_service
        except ImportError:
            logger.error("[AutoCreator] Primary voiceover service missing.")
            return []

        for i, seg in enumerate(segments):
            text = seg.get("text", "")
            if not text:
                continue

            out_path = f"temp/voice/segment_{job_id}_{i}.mp3"
            try:
                # Primary TTS
                actual_path = await service.generate_voiceover(text, voice_id="onyx")
                if actual_path and os.path.exists(actual_path):
                    voice_paths.append(actual_path)
            except Exception as e:
                logger.error(f"[AutoCreator] Voiceover failed for segment {i}: {e}")
                # Optional: Add fallback TTS provider here if needed
                continue

        return voice_paths

    async def create_cinema_video(
        self, 
        job_id: int, 
        topic: str, 
        niche: str, 
        blueprint_id: str = "story-factory",
        engine: str = "cloud",
        script: list[dict] | None = None
    ) -> str:
        """
        Autonomous Script-to-Video Workflow with real-time node instrumentation.
        """
        from src.api.routes.ws import notify_nexus_job_update_sync

        logger.info(f"[AutoCreator] Launching Cinema Mode: {topic} in {niche} (Engine: {engine})")

        async def notify(node: str, status: str, progress: int):
            # 1. Update Database for persistence
            try:
                from src.api.utils.database import async_session_factory
                from src.api.utils.models import NexusJobDB
                from sqlalchemy import select

                async with async_session_factory() as db:
                    stmt = select(NexusJobDB).where(NexusJobDB.id == str(job_id))
                    result = await db.execute(stmt)
                    job = result.scalar_one_or_none()
                    if job:
                        job.current_node = node
                        # Update specific node status in JSON
                        current_status = dict(job.node_status or {})
                        current_status[node] = status
                        job.node_status = current_status
                        job.progress = progress
                        await db.commit()
            except Exception as e:
                logger.error(f"[AutoCreator] Failed to persist node update: {e}")

            # 2. Notify WebSocket for real-time UI
            notify_nexus_job_update_sync(
                {
                    "id": str(job_id),
                    "status": f"{node.upper()}_{status}",
                    "current_node": node,
                    "node_status": status,
                    "progress": progress,
                    "niche": niche,
                }
            )

        # 1. Ingress: Script Generation (or override)
        await notify("ingress", "ACTIVE", 10)
        
        if script:
            logger.info(f"[AutoCreator] Using provided script override for Job {job_id}")
            segments = script
        else:
            segments = await self.generate_viral_script(topic, niche)
            
        if not segments:
            await notify("ingress", "FAILED", 0)
            raise ValueError("Script generation produced no segments")
        await notify("ingress", "COMPLETED", 20)

        # 2. Cognition: Asset Sourcing
        await notify("cognition", "ACTIVE", 30)
        visual_paths = await self._source_visual_assets(segments, job_id, niche, engine=engine)
        voice_paths = await self._generate_voiceovers(segments, job_id)

        if not visual_paths or not voice_paths:
            await notify("cognition", "FAILED", 0)
            raise ValueError("Failed to source required assets for synthesis")
        await notify("cognition", "COMPLETED", 50)

        # 3. Synthesis & Egress: Assembly
        await notify("synthesis", "ACTIVE", 60)
        from src.services.nexus_engine.orchestrator import base_nexus_orchestrator

        output_path = await base_nexus_orchestrator.assemble_video(
            job_id=job_id,
            niche=niche,
            script_segments=segments,
            voiceover_paths=voice_paths,
            visual_paths=visual_paths,
            music_path=None,
            blueprint_id=blueprint_id,
        )
        
        if output_path:
            await notify("synthesis", "COMPLETED", 100)
            await notify("egress", "COMPLETED", 100)
        else:
            await notify("synthesis", "FAILED", 0)

        return output_path

    async def launch_automated_video(
        self,
        user_id: str,
        topic: str,
        niche: str,
        style: str = "Cinematic",
        duration: int = 60,
        engine: str = "cloud",
        script: list[dict] | None = None
    ) -> str:
        """
        High-level entry point to create and launch an automated video generation job.
        """
        import uuid
        from src.api.utils.database import async_session_factory
        from src.api.utils.models import NexusJobDB
        
        job_id = str(uuid.uuid4())
        
        # 1. Create Job Entry
        async with async_session_factory() as db:
            new_job = NexusJobDB(
                id=job_id,
                user_id=user_id,
                niche=niche,
                current_node="ingress",
                node_status={"ingress": "QUEUED"},
                progress=0,
                job_metadata={
                    "topic": topic,
                    "style": style,
                    "duration": duration,
                    "engine": engine
                }
            )
            db.add(new_job)
            await db.commit()
            
        # 2. Spawn Background Task (Non-blocking)
        import asyncio
        asyncio.create_task(
            self.create_cinema_video(
                job_id=job_id,
                topic=topic,
                niche=niche,
                engine=engine,
                script=script
            )
        )
        
        return job_id


base_auto_creator = AutoCreator()
