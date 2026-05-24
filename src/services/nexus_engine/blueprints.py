import logging
import asyncio
import time
from typing import Any, Dict, List, Protocol, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.api.utils.models import BlueprintDB

logger = logging.getLogger(__name__)

# --- Protocol / Base Class for Node Handlers ---

class NodeHandler(Protocol):
    async def execute(self, inputs: dict, previous_results: dict, job_id: str) -> dict:
        ...

# --- Registry for Node Handlers ---

class NodeHandlerRegistry:
    def __init__(self):
        self._handlers: Dict[str, Type[NodeHandler]] = {}
        self._blueprint_overrides: Dict[str, Dict[str, Type[NodeHandler]]] = {}

    def register(self, node_type: str, handler_class: Type[NodeHandler], blueprint_id: str = None):
        if blueprint_id:
            if blueprint_id not in self._blueprint_overrides:
                self._blueprint_overrides[blueprint_id] = {}
            self._blueprint_overrides[blueprint_id][node_type] = handler_class
        else:
            self._handlers[node_type] = handler_class

    def get_handler(self, node_type: str, blueprint_id: str) -> NodeHandler:
        # Check for blueprint-specific override first
        if blueprint_id in self._blueprint_overrides and node_type in self._blueprint_overrides[blueprint_id]:
            return self._blueprint_overrides[blueprint_id][node_type]()
        
        # Fallback to generic handler
        handler_class = self._handlers.get(node_type)
        if not handler_class:
            raise ValueError(f"No handler registered for node type: {node_type}")
        return handler_class()

registry = NodeHandlerRegistry()

# --- Specialized Handlers ---

class DefaultIngressHandler:
    async def execute(self, inputs: dict, previous_results: dict, job_id: str) -> dict:
        return {
            "input_validated": True,
            "data_type": inputs.get("data_type", "unknown"),
            "input_size": len(str(inputs)),
        }

class DefaultCognitionHandler:
    async def execute(self, inputs: dict, previous_results: dict, job_id: str) -> dict:
        from src.services.llm.intelligence_hub import base_intelligence_service

        content = inputs.get("content", "")
        prompt = f"Analyze and process the following content: {str(content)[:500]}..."

        try:
            response = await base_intelligence_service.chat(
                prompt=prompt,
                system_prompt="You are a content analyst. Analyze the given content and provide insights.",
                complexity="low",
            )
            return {
                "ai_processed": True,
                "analysis": response.get("response", ""),
                "confidence": 0.85,
            }
        except Exception as e:
            logger.warning(f"[DefaultCognitionHandler] IntelligenceHub call failed: {e}")
            return {"ai_processed": False, "fallback": "AI unavailable", "error": str(e)}

class TopicFusionCognitionHandler:
    async def execute(self, inputs: dict, previous_results: dict, job_id: str) -> dict:
        from src.engines.topic_fusion_orchestrator import base_topic_fusion_orchestrator
        topic = inputs.get("topic") or inputs.get("niche")
        scenes = await base_topic_fusion_orchestrator.decompose_topic_into_scenes(topic)
        return {"ai_processed": True, "scenes": scenes, "scenes_generated": len(scenes)}

class DefaultSynthesisHandler:
    async def execute(self, inputs: dict, previous_results: dict, job_id: str) -> dict:
        from src.services.video_engine.synthesis_service import GenerativeService
        service = GenerativeService()
        engine = inputs.get("engine", "ltx-video")
        prompt = inputs.get("content") or inputs.get("visual_prompt")
        
        video_path = await service.synthesize_video(
            prompt=prompt or "Cinematic cityscape",
            engine=engine,
            aspect_ratio=inputs.get("aspect_ratio", "16:9")
        )
        return {"output_generated": True, "video_path": video_path, "engine": engine}

class TopicFusionSynthesisHandler:
    async def execute(self, inputs: dict, previous_results: dict, job_id: str) -> dict:
        from src.services.video_engine.scene_orchestrator import base_scene_orchestrator_service
        from src.services.video_engine.synthesis_service import base_generative_service
        
        topic = inputs.get("topic") or inputs.get("niche")
        cognition_res = previous_results.get("cognition", {})
        scenes = cognition_res.get("scenes", [])
        
        # 1. Try Scene-Based Fusion (Discovery + Pexels)
        fusion_result = await base_scene_orchestrator_service.produce_scene_based_video(
            scenes=scenes,
            niche=inputs.get("niche", topic)
        )
        
        # 2. AI Fallback: If fusion failed because no assets were found, generate using AI
        if not fusion_result.get("success") and fusion_result.get("reason") == "No compatible video files found or processing failed":
            logger.warning("🔄 [Blueprint] Discovery failed. Triggering AI Video Generation fallback...")
            
            # Use the first scene's prompt for a short AI video
            fallback_prompt = scenes[0].get("visual_prompt", topic) if scenes else topic
            video_path = await base_generative_service.synthesize_video(
                prompt=fallback_prompt,
                engine="hunyuan", # Default reliable internal engine
                aspect_ratio="9:16"
            )
            
            if video_path:
                return {
                    "output_generated": True,
                    "video_path": video_path,
                    "method": "ai_generation_fallback",
                    "fusion_details": fusion_result
                }

        return {
            "output_generated": fusion_result.get("success", False),
            "video_path": fusion_result.get("video_path"),
            "fusion_details": fusion_result
        }

class DefaultEgressHandler:
    async def execute(self, inputs: dict, previous_results: dict, job_id: str) -> dict:
        synthesis = previous_results.get("synthesis", {})
        video_path = synthesis.get("video_path")
        return {
            "finalized": True,
            "output_path": video_path,
            "summary": f"Blueprint execution completed. Video saved to {video_path}",
        }

# --- Register Handlers ---

registry.register("ingress", DefaultIngressHandler)
registry.register("cognition", DefaultCognitionHandler)
registry.register("cognition", TopicFusionCognitionHandler, blueprint_id="topic-fusion")
registry.register("synthesis", DefaultSynthesisHandler)
registry.register("synthesis", TopicFusionSynthesisHandler, blueprint_id="topic-fusion")
registry.register("egress", DefaultEgressHandler)

# --- Fallback Blueprints ---

FALLBACK_BLUEPRINTS = [
    {
        "id": "viral-reskin",
        "name": "Viral Re-skinner",
        "description": "Auto-discovery of high-velocity clips with neural style injection.",
        "composition_id": "ViralClip",
        "nodes": [
            {"type": "ingress", "label": "Deep Discovery", "desc": "Scanning TikTok clusters."},
            {"type": "cognition", "label": "Viral DNA Match", "desc": "Llama-3 analysis."},
            {"type": "synthesis", "label": "Neural Remix", "desc": "Applying cinematic overlays."},
            {"type": "egress", "label": "Global Sync", "desc": "Scheduled dispatch."},
        ],
    },
    {
        "id": "topic-fusion",
        "name": "Topic Narrative Fusion",
        "description": "Transforms a single topic into a 10-scene viral masterpiece using autonomous asset discovery.",
        "composition_id": "ViralClip",
        "nodes": [
            {"type": "ingress", "label": "Topic Analysis", "desc": "Analyzing niche relevance."},
            {"type": "cognition", "label": "Narrative Decompose", "desc": "Breaking topic into 10 scenes."},
            {"type": "synthesis", "label": "Swarm Discovery", "desc": "Finding viral video assets."},
            {"type": "egress", "label": "Neural Fusion", "desc": "Stitching segments."},
        ],
    },
]

# --- Core API ---

async def get_blueprints(db: AsyncSession) -> list[dict]:
    stmt = select(BlueprintDB)
    result = await db.execute(stmt)
    blueprints = result.scalars().all()
    if not blueprints:
        return FALLBACK_BLUEPRINTS
    return [{"id": bp.id, "name": bp.name, "description": bp.description, "nodes": bp.nodes} for bp in blueprints]

async def execute_blueprint(blueprint: dict, inputs: dict, job_id: str) -> dict:
    from src.api.routes.ws import notify_nexus_job_update_sync
    results = {}
    nodes = blueprint.get("nodes", [])
    blueprint_id = blueprint.get("id", "unknown")

    try:
        for i, node in enumerate(nodes):
            node_type = node.get("type", "unknown")
            node_label = node.get("label", node_type)
            progress = int(((i + 1) / len(nodes)) * 100)

            notify_nexus_job_update_sync({
                "id": str(job_id),
                "status": f"EXECUTING_{node_type.upper()}",
                "current_node": node_type.lower(),
                "progress": progress,
            })

            handler = registry.get_handler(node_type, blueprint_id)
            node_result = await handler.execute(inputs, results, job_id)
            results[node_type] = node_result
            
            # Special case: map 'scenes' from cognition to result top level if needed by synthesis
            if node_type == "cognition" and "scenes" in node_result:
                results["scenes"] = node_result["scenes"]
                
                # SAVE SCENES TO DATABASE FOR PREVIEW
                from src.api.utils.database import async_session_factory
                from src.api.utils.models import NexusJobDB
                from sqlalchemy import select
                
                async with async_session_factory() as db:
                    stmt = select(NexusJobDB).where(NexusJobDB.id == job_id)
                    result = await db.execute(stmt)
                    job = result.scalar_one_or_none()
                    
                    if job:
                        metadata = job.job_metadata or {}
                        metadata["preview_scenes"] = node_result["scenes"]
                        job.job_metadata = metadata
                        await db.commit()

        return {"status": "success", "results": results, "blueprint_id": blueprint_id}
    except Exception as e:
        logger.error(f"[Blueprint] Execution failed for job {job_id}: {e}")
        return {"status": "failed", "error": str(e), "blueprint_id": blueprint_id}

async def get_blueprint_by_id(db: AsyncSession, blueprint_id: str) -> dict | None:
    stmt = select(BlueprintDB).where(BlueprintDB.id == blueprint_id)
    result = await db.execute(stmt)
    bp = result.scalar_one_or_none()
    if not bp:
        return next((fb for fb in FALLBACK_BLUEPRINTS if fb["id"] == blueprint_id), FALLBACK_BLUEPRINTS[0])
    return {"id": bp.id, "name": bp.name, "description": bp.description, "nodes": bp.nodes}
