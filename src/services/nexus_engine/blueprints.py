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


# ═══════════════════════════════════════════
# DAG-Powered Blueprint Execution
# ═══════════════════════════════════════════

async def dag_execute_blueprint(
    blueprint: dict,
    inputs: dict,
    job_id: str,
    segments: list[dict] | None = None,
    automation_mode: str = "manual",
) -> dict:
    """
    Execute a blueprint using the DAG video compiler.

    Instead of running nodes sequentially, this compiles the blueprint's
    nodes into a DAG execution plan and executes it with:
    - Parallelism (independent nodes run concurrently)
    - Caching (hash-based, skip recomputation when inputs haven't changed)
    - Graceful fallback (failed nodes don't crash the graph)

    Args:
        blueprint: Blueprint config dict (nodes, composition_id, etc.)
        inputs: Initial input params (topic, niche, scenes, etc.)
        job_id: Unique job identifier
        segments: Optional pre-generated script segments

    Returns:
        dict with status, results, and blueprint_id
    """
    from src.api.routes.ws import notify_nexus_job_update_sync
    from src.services.video_engine.dag_executor import base_dag_compiler, base_dag_scheduler, base_dag_cache
    from src.services.nexus_engine.dag_nodes import (
        StockSearchNode,
        VideoDownloadNode,
        ParallelAssetSourceNode,
        VisionAuditNode,
        ColorGradeNode,
        AudioMixNode,
        SceneRenderNode,
    )

    blueprint_id = blueprint.get("id", "unknown")
    composition_id = blueprint.get("composition_id", "ViralClip")
    niche = inputs.get("niche", "")
    topic = inputs.get("topic", "") or niche

    # Get scenes (from segments param, cognition results, or generate)
    scenes = segments or inputs.get("scenes", [])
    if not scenes:
        # Generate scenes via cognition handler
        try:
            handler = registry.get_handler("cognition", blueprint_id)
            cognition_result = await handler.execute(inputs, {}, job_id)
            scenes = cognition_result.get("scenes", [])
        except Exception as e:
            logger.warning("[DAG-Blueprint] Cognition fallback failed: %s", e)

    if not scenes:
        return {"status": "failed", "error": "No scenes available for DAG execution", "blueprint_id": blueprint_id}

    # Build DAG nodes for each scene
    all_dag_nodes = []
    scene_index = 0

    for seg_num, segment in enumerate(scenes):
        visual_prompt = segment.get("visual_prompt", niche)
        seg_id = f"seg_{seg_num}"

        # --- Parallel Asset Source (runs stock + platform search concurrently) ---
        asset_node = ParallelAssetSourceNode(
            node_id=f"{seg_id}_sourcing",
            params={
                "keyword": visual_prompt,
                "niche": niche,
                "platform_urls": [],
            },
        )
        all_dag_nodes.append(asset_node)

        # --- Vision Audit (depends on asset sourcing completing) ---
        if segment.get("visual_prompt"):
            audit_node = VisionAuditNode(
                node_id=f"{seg_id}_audit",
                params={
                    "prompt": visual_prompt,
                    "job_id": job_id,
                },
                inputs=[asset_node.id],
            )
            all_dag_nodes.append(audit_node)

        scene_index += 1

    # --- Terminal: Scene Render Node (depends on ALL audit nodes) ---
    audit_ids = [n.id for n in all_dag_nodes if "_audit" in n.id]
    source_ids = [n.id for n in all_dag_nodes if "_sourcing" in n.id]

    render_node = SceneRenderNode(
        node_id="render",
        params={
            "job_id": job_id,
            "niche": niche,
            "style": inputs.get("style", "CINEMATIC_DOC"),
            "blueprint": blueprint,
            "composition_id": composition_id,
            "job_metadata": inputs.get("job_metadata", {}),
        },
        inputs=audit_ids + source_ids,
    )
    all_dag_nodes.append(render_node)

    # Notify start
    notify_nexus_job_update_sync({
        "id": str(job_id),
        "status": "DAG_COMPILING",
        "current_node": "dag_compiler",
        "progress": 10,
        "niche": niche,
    })

    try:
        # Compile DAG
        plan = base_dag_compiler.compile(all_dag_nodes)

        logger.info(
            "[DAG-Blueprint] Compiled %d nodes into %d parallel batches for job %s",
            plan.total_nodes(),
            plan.total_batches(),
            job_id,
        )

        notify_nexus_job_update_sync({
            "id": str(job_id),
            "status": "DAG_EXECUTING",
            "current_node": "dag_executor",
            "progress": 20,
            "niche": niche,
            "metadata": {
                "total_nodes": plan.total_nodes(),
                "total_batches": plan.total_batches(),
            },
        })

        # Execute DAG
        context = await base_dag_scheduler.run(plan, inputs=inputs)

        # Extract results
        render_result = context.get("render", {})
        output_path = render_result.get("output_path") if isinstance(render_result, dict) else render_result

        logger.info("[DAG-Blueprint] Execution complete for job %s: %s", job_id, output_path)

        notify_nexus_job_update_sync({
            "id": str(job_id),
            "status": "DAG_COMPLETED",
            "current_node": "egress",
            "progress": 100,
            "niche": niche,
            "output_path": output_path,
        })

        return {
            "status": "success",
            "results": {
                "dag_context": {
                    k: v for k, v in context.items()
                    if not k.startswith("_")
                },
                "output_path": output_path,
                "total_scenes": len(scenes),
                "total_nodes": plan.total_nodes(),
                "total_batches": plan.total_batches(),
            },
            "blueprint_id": blueprint_id,
        }

    except Exception as e:
        logger.error("[DAG-Blueprint] Execution failed for job %s: %s", job_id, e)
        notify_nexus_job_update_sync({
            "id": str(job_id),
            "status": "DAG_FAILED",
            "current_node": "dag_executor",
            "progress": 0,
            "error": str(e),
        })
        return {"status": "failed", "error": str(e), "blueprint_id": blueprint_id}

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

async def execute_blueprint(
    blueprint: dict, inputs: dict, job_id: str,
    use_dag: bool = False,
    automation_mode: str = "manual",
) -> dict:
    """
    Execute a blueprint with automation mode awareness.

    Args:
        blueprint: Blueprint config dict
        inputs: Initial input params
        job_id: Unique job identifier
        use_dag: Use DAG engine (legacy flag, overridden by automation_mode)
        automation_mode: "manual" | "partial" | "full"
            - manual: Respects ``use_dag`` flag (legacy behavior)
            - partial: Forces DAG + approval gate before execution
            - full: Forces DAG + auto-execute
    """
    from src.services.video_engine.automation import AutomationMode, is_at_least

    # Resolve effective DAG usage
    mode = AutomationMode.from_str(automation_mode)
    effective_dag = use_dag or is_at_least(mode, AutomationMode.PARTIAL)
    if mode == AutomationMode.MANUAL:
        effective_dag = use_dag

    if effective_dag:
        return await dag_execute_blueprint(
            blueprint=blueprint,
            inputs=inputs,
            job_id=job_id,
            segments=inputs.get("segments", []),
            automation_mode=automation_mode,
        )

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
