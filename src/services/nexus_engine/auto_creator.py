import json
import logging
import os
import asyncio
import cv2
from typing import List, Dict, Any
import tenacity
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.api.config import settings
from src.api.utils.resilience import CircuitBreaker
from src.services.llm.service import LLMProvider

logger = logging.getLogger(__name__)


class AutoCreator:
    """
    Autonomous Video Creation Engine.
    Hardened with Circuit Breakers and retries for production-grade reliability.
    Orchestrates LLM, Video, and Voiceover services.
    """
    
    def __init__(self):
        self.breaker = CircuitBreaker(name="AutoCreator-Pipeline", failure_threshold=3, recovery_timeout=300)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=5, max=30),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def generate_viral_script(self, topic: str, niche: str, duration_seconds: int = 60, style: str = "CINEMATIC_DOC") -> List[Dict[str, Any]]:
        """
        Generates a multi-part viral script with resilience.
        """
        from .style_library import get_style
        style_config = get_style(style)
        
        num_chapters = max(1, duration_seconds // 60)
        all_segments = []
        
        logger.info(f"[AutoCreator] Generating {num_chapters} chapters for style: {style}")

        for i in range(num_chapters):
            context = f"Topic: {topic}. Niche: {niche}. Style: {style_config['name']}. {style_config['prompt_modifier']}"
            if all_segments:
                last_segment = all_segments[-1].get("text", "")
                context += f" Previous context: {last_segment[-200:]}"
            
            part_segments = await self._generate_script_part(
                topic, niche, duration_seconds, f"Chapter {i+1}", context=context, style=style
            )
            
            if part_segments:
                all_segments.extend(part_segments)
            
        if not all_segments:
            raise RuntimeError("Script generation returned no segments after multiple attempts.")
            
        return all_segments

    async def _generate_script_part(
        self, topic: str, niche: str, duration: int, chapter_info: str, context: str = "", style: str = "CINEMATIC_DOC"
    ) -> list[dict]:
        from src.services.llm.intelligence_hub import base_intelligence_service
        from .style_library import get_style
        style_config = get_style(style)

        system_prompt = f"You are a professional video scriptwriter for the {niche} niche. Your style is: {style_config['name']}."
        prompt = f"""
        Topic: {topic}
        Style: {style_config['name']} ({style_config['description']})
        Tone: {style_config['prompt_modifier']}
        Target Duration: {duration} seconds
        Part Info: {chapter_info}
        {context}
        
        Generate a JSON object with a 'segments' key. This key MUST contain a list of 6 to 8 segments.
        Each segment MUST have: 'text', 'visual_prompt', 'mood', 'type'.
        
        OUTPUT FORMAT (JSON ONLY):
        {{ "segments": [ ... ] }}
        """

        try:
            response = await base_intelligence_service.chat(
                prompt=prompt,
                system_prompt=system_prompt,
                json_mode=True,
                complexity="high"
            )
            
            content = json.loads(response["response"])
            segments = []
            if isinstance(content, list):
                segments = content
            elif isinstance(content, dict):
                segments = content.get("segments", content.get("script", [content]))
            
            return segments
        except Exception as e:
            logger.error(f"[AutoCreator] _generate_script_part error: {e}")
            raise

    async def create_cinema_video(
        self, 
        job_id: str, 
        topic: str, 
        niche: str, 
        user_id: str | None = None,
        blueprint_id: str = "story-factory",
        engine: str = "cloud",
        script: list[dict] | None = None,
        use_gpu: bool = False,
        batch_count: int = 1,
        duration_seconds: int = 60,
        style: str = "CINEMATIC_DOC"
    ) -> str:
        """
        Main creation loop protected by CircuitBreaker.
        """
        if self.breaker.is_open():
            logger.error("[AutoCreator] Circuit OPEN. Creation denied.")
            raise RuntimeError("AutoCreator is temporarily unavailable.")

        try:
            result = await self._create_cinema_video_inner(
                job_id, topic, niche, user_id, blueprint_id, engine, script, use_gpu, batch_count, duration_seconds, style
            )
            self.breaker.record_success()
            return result
        except Exception as e:
            self.breaker.record_failure()
            logger.error(f"[AutoCreator] Creation Pipeline Failed: {e}")
            raise

    async def _create_cinema_video_inner(self, job_id, topic, niche, user_id, blueprint_id, engine, script, use_gpu, batch_count, duration_seconds, style) -> str:
        from src.api.routes.ws import notify_nexus_job_update_sync
        from src.api.utils.database import async_session_factory
        from src.api.utils.models import NexusJobDB
        from sqlalchemy import select

        async def notify(node: str, status: str, progress: int):
            try:
                async with async_session_factory() as db:
                    stmt = select(NexusJobDB).where(NexusJobDB.id == str(job_id))
                    result = await db.execute(stmt)
                    job = result.scalar_one_or_none()
                    if job:
                        job.current_node = node
                        current_status = dict(job.node_status or {})
                        current_status[node] = status
                        job.node_status = current_status
                        job.progress = progress
                        await db.commit()
            except Exception as e:
                logger.error(f"[AutoCreator] DB notify error: {e}")

            notify_nexus_job_update_sync({
                "id": str(job_id),
                "status": f"{node.upper()}_{status}",
                "current_node": node,
                "node_status": status,
                "progress": progress
            })

        # 1. Ingress
        await notify("ingress", "ACTIVE", 10)
        if script:
            segments = script
        else:
            segments = await self.generate_viral_script(topic, niche, duration_seconds=duration_seconds, style=style)
        await notify("ingress", "COMPLETED", 20)

        # 2. Cognition
        await notify("cognition", "ACTIVE", 30)
        visual_paths = await self._source_visual_assets(segments, job_id, niche, engine=engine, style=style)
        voice_paths = await self._generate_voiceovers(segments, job_id, style=style)
        
        if not visual_paths or not voice_paths:
            raise ValueError("Asset sourcing failed.")
        await notify("cognition", "COMPLETED", 50)

        # 3. Synthesis
        await notify("synthesis", "ACTIVE", 60)
        from src.services.nexus_engine.orchestrator import base_nexus_service
        
        from .style_library import get_style
        style_config = get_style(style)
        vfx_type = style_config.get("remotion_flags", {}).get("vfx", "default")

        output_path = await base_nexus_service.assemble_video(
            job_id=job_id,
            niche=niche,
            script_segments=segments,
            voiceover_paths=voice_paths,
            visual_paths=visual_paths,
            music_path=None,
            blueprint_id=blueprint_id,
            style=style,
            job_metadata={"vfx": vfx_type}
        )

        if not output_path:
            raise RuntimeError("Assembly failed.")
            
        await notify("synthesis", "COMPLETED", 90)
        
        # 4. Egress
        await notify("egress", "ACTIVE", 95)
        # Final output path persistence
        async with async_session_factory() as db:
            stmt = select(NexusJobDB).where(NexusJobDB.id == str(job_id))
            result = await db.execute(stmt)
            job = result.scalar_one_or_none()
            if job:
                job.job_metadata["output_path"] = output_path
                await db.commit()
                
        await notify("egress", "COMPLETED", 100)
        return output_path

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=5, max=60),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def publish_job(self, job_id: str, platforms: list[str] = ["youtube"]) -> dict:
        """Publishes a completed job with resilience."""
        from src.services.publishing.service import base_publishing_service
        from src.api.utils.database import async_session_factory
        from src.api.utils.models import NexusJobDB
        from sqlalchemy import select

        async with async_session_factory() as db:
            stmt = select(NexusJobDB).where(NexusJobDB.id == job_id)
            result = await db.execute(stmt)
            job = result.scalar_one_or_none()
            
            if not job or "output_path" not in job.job_metadata:
                raise ValueError("Job not ready for publishing.")

            output_path = job.job_metadata["output_path"]
            publish_results = {}
            
            for platform in platforms:
                try:
                    res = await base_publishing_service.publish_to_platform(
                        user_id=job.user_id,
                        platform=platform,
                        video_path=output_path,
                        metadata={"title": job.job_metadata.get("topic", "EttaMetta Viral Video")}
                    )
                    publish_results[platform] = res
                except Exception as e:
                    publish_results[platform] = {"status": "error", "message": str(e)}

            job.job_metadata["publish_results"] = publish_results
            await db.commit()
            return publish_results

    # Keep helper methods but ensure they use logging
    async def _source_visual_assets(self, segments, job_id, niche, engine, style):
        from src.services.video_engine.stock_service import base_stock_service
        from src.services.llm.service import unified_llm_service
        
        visual_paths = []
        for i, seg in enumerate(segments):
            prompt = seg.get("visual_prompt", niche)
            logger.info(f"[AutoCreator] Sourcing visual for segment {i}: {prompt}")
            
            # Fetch up to 3 candidates for re-roll
            urls = await base_stock_service.fetch_b_roll(prompt, count=3)
            if not urls:
                logger.warning(f"[AutoCreator] No stock found for: {prompt}. Using fallback.")
                urls = await base_stock_service.fetch_b_roll(niche, count=1)
            
            best_path = None
            for attempt, url in enumerate(urls):
                path = await base_stock_service.download_stock_video(url)
                if not path:
                    continue
                
                # Perform Hard Vision Audit
                is_relevant = await self._vision_audit(path, seg.get("visual_prompt", niche), job_id, i)
                if is_relevant:
                    logger.info(f"[AutoCreator] Segment {i} passed audit on attempt {attempt+1}")
                    best_path = path
                    break
                else:
                    logger.warning(f"[AutoCreator] Segment {i} failed audit on attempt {attempt+1}. Re-rolling...")
                    # Clean up the failed clip to save space
                    if os.path.exists(path):
                        os.remove(path)
            
            if best_path:
                visual_paths.append(best_path)
            else:
                # If all 3 fail, try one last time with generic niche prompt and skip audit
                logger.error(f"[AutoCreator] Segment {i} exhausted re-rolls. Falling back to generic.")
                fallback_urls = await base_stock_service.fetch_b_roll(niche, count=1)
                if fallback_urls:
                    f_path = await base_stock_service.download_stock_video(fallback_urls[0])
                    if f_path: visual_paths.append(f_path)
        
        return visual_paths

    async def _vision_audit(self, video_path: str, visual_prompt: str, job_id: str, segment_idx: int) -> bool:
        """
        Extracts a frame and audits it against the visual prompt using Gemini Flash.
        """
        from src.services.llm.service import unified_llm_service
        
        audit_frame_dir = "temp/audit_source"
        os.makedirs(audit_frame_dir, exist_ok=True)
        frame_path = f"{audit_frame_dir}/audit_{job_id}_{segment_idx}.jpg"
        
        try:
            # Extract middle frame
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return True # Fallback to true if extraction fails to avoid stuck loops
                
            cv2.imwrite(frame_path, frame)
            
            # AI Audit with Fallback
            prompt = f"Does this video frame match the description: '{visual_prompt}'? Answer with YES or NO followed by a short reason."
            
            try:
                audit_result = await unified_llm_service.analyze_image(frame_path, prompt, provider=LLMProvider.GEMINI)
                if "error" in audit_result or not audit_result.get("content"):
                    raise RuntimeError("Gemini vision audit failed")
            except Exception as e:
                logger.warning(f"[AutoCreator] Gemini vision failed, falling back to Ollama: {e}")
                audit_result = await unified_llm_service.analyze_image(
                    frame_path, prompt, provider=LLMProvider.OLLAMA, model="llama3.2-vision"
                )
            
            content = audit_result.get("content", "YES").upper()
            
            # Clean up frame
            if os.path.exists(frame_path):
                os.remove(frame_path)
                
            return "YES" in content
        except Exception as e:
            logger.error(f"[AutoCreator] Vision audit error: {e}")
            return True # Bypassed on error

    async def _generate_voiceovers(self, segments, job_id, style):
        from src.services.voiceover.service import base_voiceover_service
        voice_paths = []
        for i, seg in enumerate(segments):
            text = seg.get("text", "")
            if text:
                path = await base_voiceover_service.generate_voiceover(text)
                if path:
                    voice_paths.append(path)
        return voice_paths

base_creator_service = AutoCreator()
