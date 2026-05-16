"""
Tests for Nexus Engine Blueprints — Handler Registry, Node Execution, and Fallback Logic.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestNodeHandlerRegistry:
    """Tests for the NodeHandlerRegistry — registration, resolution, overrides."""

    def test_register_and_get_handler(self):
        """Register a handler and retrieve it by node_type."""
        from src.services.nexus_engine.blueprints import NodeHandlerRegistry

        registry = NodeHandlerRegistry()

        class TestHandler:
            async def execute(self, inputs, previous_results, job_id):
                return {"result": "ok"}

        registry.register("test_node", TestHandler)
        handler = registry.get_handler("test_node", "any-blueprint")

        assert handler is not None
        assert hasattr(handler, 'execute')

    def test_get_handler_raises_for_unregistered(self):
        """Asking for an unregistered node_type raises ValueError."""
        from src.services.nexus_engine.blueprints import NodeHandlerRegistry

        registry = NodeHandlerRegistry()

        with pytest.raises(ValueError, match="No handler registered"):
            registry.get_handler("nonexistent_node", "any-blueprint")

    def test_blueprint_specific_override(self):
        """Blueprint-specific handler takes precedence over generic handler."""
        from src.services.nexus_engine.blueprints import NodeHandlerRegistry

        registry = NodeHandlerRegistry()

        class GenericHandler:
            async def execute(self, inputs, previous_results, job_id):
                return {"source": "generic"}

        class OverrideHandler:
            async def execute(self, inputs, previous_results, job_id):
                return {"source": "override"}

        registry.register("cognition", GenericHandler)
        registry.register("cognition", OverrideHandler, blueprint_id="special-fusion")

        # Generic blueprint gets generic handler
        generic = registry.get_handler("cognition", "some-other-blueprint")
        result = self._run_async(generic.execute({}, {}, "job-1"))
        assert result["source"] == "generic"

        # Special blueprint gets override
        override = registry.get_handler("cognition", "special-fusion")
        result = self._run_async(override.execute({}, {}, "job-1"))
        assert result["source"] == "override"

    def test_multiple_blueprint_overrides(self):
        """Multiple blueprints can each have their own overrides."""
        from src.services.nexus_engine.blueprints import NodeHandlerRegistry

        registry = NodeHandlerRegistry()

        class HandlerA:
            async def execute(self, inputs, prev, jid):
                return {"handler": "A"}

        class HandlerB:
            async def execute(self, inputs, prev, jid):
                return {"handler": "B"}

        registry.register("egress", HandlerA, blueprint_id="blueprint-a")
        registry.register("egress", HandlerB, blueprint_id="blueprint-b")

        ha = registry.get_handler("egress", "blueprint-a")
        hb = registry.get_handler("egress", "blueprint-b")
        assert ha.execute({}, {}, "x") is not None
        assert hb.execute({}, {}, "x") is not None

    @staticmethod
    def _run_async(coro):
        """Helper to run an async coroutine synchronously."""
        import asyncio
        return asyncio.run(coro)


class TestDefaultHandlers:
    """Tests for the built-in default handlers."""

    @pytest.mark.asyncio
    async def test_ingress_validates_input(self):
        """DefaultIngressHandler returns validated result with input metadata."""
        from src.services.nexus_engine.blueprints import DefaultIngressHandler

        handler = DefaultIngressHandler()
        result = await handler.execute(
            {"data_type": "video", "content": "test"},
            {},
            "job-001"
        )

        assert result["input_validated"] is True
        assert result["data_type"] == "video"
        assert result["input_size"] > 0

    @pytest.mark.asyncio
    async def test_ingress_unknown_data_type(self):
        """DefaultIngressHandler returns 'unknown' when no data_type provided."""
        from src.services.nexus_engine.blueprints import DefaultIngressHandler

        handler = DefaultIngressHandler()
        result = await handler.execute({"random": "data"}, {}, "job-002")

        assert result["data_type"] == "unknown"

    @pytest.mark.asyncio
    async def test_egress_extracts_video_path(self):
        """DefaultEgressHandler extracts video_path from synthesis results."""
        from src.services.nexus_engine.blueprints import DefaultEgressHandler

        handler = DefaultEgressHandler()
        result = await handler.execute(
            {},
            {"synthesis": {"video_path": "/tmp/output.mp4"}},
            "job-003"
        )

        assert result["finalized"] is True
        assert result["output_path"] == "/tmp/output.mp4"
        assert "Video saved to" in result["summary"]

    @pytest.mark.asyncio
    async def test_egress_no_video_path(self):
        """DefaultEgressHandler handles missing video_path gracefully."""
        from src.services.nexus_engine.blueprints import DefaultEgressHandler

        handler = DefaultEgressHandler()
        result = await handler.execute({}, {"synthesis": {}}, "job-004")

        assert result["finalized"] is True
        assert result["output_path"] is None


class TestExecuteBlueprint:
    """Tests for the execute_blueprint orchestrator function."""

    @pytest.mark.asyncio
    async def test_execute_simple_blueprint(self):
        """Execute all nodes in a blueprint sequentially and return results."""
        from src.services.nexus_engine.blueprints import execute_blueprint

        blueprint = {
            "id": "test-blueprint",
            "nodes": [
                {"type": "ingress", "label": "Check Input"},
                {"type": "egress", "label": "Finalize"},
            ]
        }

        # Patch at the source module, not the consumer module
        with patch("src.api.routes.ws.notify_nexus_job_update_sync", new_callable=MagicMock):
            result = await execute_blueprint(blueprint, {"content": "test"}, "job-005")

        assert result["status"] == "success"
        assert "ingress" in result["results"]
        assert "egress" in result["results"]
        assert result["blueprint_id"] == "test-blueprint"

    @pytest.mark.asyncio
    async def test_execute_blueprint_node_failure(self):
        """When a node fails, the blueprint returns failed status with error."""
        from src.services.nexus_engine.blueprints import NodeHandlerRegistry, execute_blueprint

        # Use a local registry with a failing handler
        local_registry = NodeHandlerRegistry()

        class IngressHandler:
            async def execute(self, inputs, previous_results, job_id):
                return {"input_validated": True, "data_type": "test"}

        class FailingHandler:
            async def execute(self, inputs, previous_results, job_id):
                raise RuntimeError("Intentional failure in test")

        local_registry.register("ingress", IngressHandler)
        local_registry.register("cognition", FailingHandler)

        blueprint = {
            "id": "failing-test",
            "nodes": [
                {"type": "ingress", "label": "Input"},
                {"type": "cognition", "label": "Fail Here"},
                {"type": "egress", "label": "Never Reached"},
            ]
        }

        # Patch at source modules
        with patch("src.api.routes.ws.notify_nexus_job_update_sync", new_callable=MagicMock):
            with patch("src.services.nexus_engine.blueprints.registry", local_registry):
                result = await execute_blueprint(blueprint, {}, "job-007")

        assert result["status"] == "failed"
        assert "error" in result
        assert "Intentional failure" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_cognition_saves_scenes_to_db(self):
        """Scenes from cognition handler get persisted to NexusJobDB."""
        from src.services.nexus_engine.blueprints import execute_blueprint

        blueprint = {
            "id": "topic-fusion",
            "nodes": [
                {"type": "cognition", "label": "Narrative Decompose"},
                {"type": "egress", "label": "Finalize"},
            ]
        }

        # Patch at the SOURCE modules (where the function body imports from)
        with patch("src.api.routes.ws.notify_nexus_job_update_sync", new_callable=MagicMock), \
             patch("src.api.utils.database.async_session_factory") as mock_session_factory, \
             patch("src.engines.topic_fusion_orchestrator.base_topic_fusion_orchestrator") as mock_tf:

            # Mock topic fusion to return scenes
            mock_tf.decompose_topic_into_scenes = AsyncMock(return_value=[{"scene": 1, "visual_prompt": "test"}])

            # Mock DB session
            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_session_factory.return_value = mock_session

            mock_job = MagicMock()
            mock_job.job_metadata = {}
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_job
            mock_session.execute.return_value = mock_result

            result = await execute_blueprint(blueprint, {"topic": "AI"}, "job-008")

        assert result["status"] == "success"
        # Verify scenes were saved to DB
        assert mock_job.job_metadata.get("preview_scenes") == [{"scene": 1, "visual_prompt": "test"}]


class TestFallbackBlueprints:
    """Tests for the FALLBACK_BLUEPRINTS list."""

    def test_fallback_blueprints_have_required_fields(self):
        """Each fallback blueprint has id, name, description, composition_id, and nodes."""
        from src.services.nexus_engine.blueprints import FALLBACK_BLUEPRINTS

        for bp in FALLBACK_BLUEPRINTS:
            assert "id" in bp
            assert "name" in bp
            assert "description" in bp
            assert "composition_id" in bp
            assert "nodes" in bp
            assert len(bp["nodes"]) > 0

    def test_fallback_blueprint_nodes_have_types(self):
        """Each node in a fallback blueprint has a type field."""
        from src.services.nexus_engine.blueprints import FALLBACK_BLUEPRINTS

        for bp in FALLBACK_BLUEPRINTS:
            for node in bp["nodes"]:
                assert "type" in node, f"Node in {bp['id']} missing 'type'"
                assert "label" in node, f"Node in {bp['id']} missing 'label'"

    def test_fallback_blueprints_ordered_preference(self):
        """Fallback blueprints are ordered with viral-reskin first, topic-fusion second."""
        from src.services.nexus_engine.blueprints import FALLBACK_BLUEPRINTS

        assert FALLBACK_BLUEPRINTS[0]["id"] == "viral-reskin"
        assert FALLBACK_BLUEPRINTS[1]["id"] == "topic-fusion"

    def test_fallback_has_viralclip_composition(self):
        """All fallback blueprints use 'ViralClip' as their composition."""
        from src.services.nexus_engine.blueprints import FALLBACK_BLUEPRINTS

        for bp in FALLBACK_BLUEPRINTS:
            assert bp["composition_id"] == "ViralClip"


class TestGetBlueprints:
    """Tests for get_blueprints and get_blueprint_by_id."""

    @pytest.mark.asyncio
    async def test_get_blueprints_returns_fallback_when_db_empty(self):
        """get_blueprints returns FALLBACK_BLUEPRINTS when DB has no blueprints."""
        from src.services.nexus_engine.blueprints import get_blueprints, FALLBACK_BLUEPRINTS

        mock_db = AsyncMock()
        mock_db_result = MagicMock()
        mock_db_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_db_result

        result = await get_blueprints(mock_db)

        assert result == FALLBACK_BLUEPRINTS

    @pytest.mark.asyncio
    async def test_get_blueprints_returns_db_blueprints(self):
        """get_blueprints returns DB blueprints when they exist."""
        from src.services.nexus_engine.blueprints import get_blueprints

        mock_bp = MagicMock()
        mock_bp.id = "custom-blueprint"
        mock_bp.name = "Custom Blueprint"
        mock_bp.description = "A custom blueprint"
        mock_bp.nodes = [{"type": "ingress", "label": "Start"}]

        mock_db = AsyncMock()
        mock_db_result = MagicMock()
        mock_db_result.scalars.return_value.all.return_value = [mock_bp]
        mock_db.execute.return_value = mock_db_result

        result = await get_blueprints(mock_db)

        assert len(result) == 1
        assert result[0]["id"] == "custom-blueprint"
        assert result[0]["name"] == "Custom Blueprint"

    @pytest.mark.asyncio
    async def test_get_blueprint_by_id_found(self):
        """get_blueprint_by_id returns the matching DB blueprint."""
        from src.services.nexus_engine.blueprints import get_blueprint_by_id

        mock_bp = MagicMock()
        mock_bp.id = "my-bp"
        mock_bp.name = "My Blueprint"
        mock_bp.description = "Desc"
        mock_bp.nodes = []

        mock_db = AsyncMock()
        mock_db_result = MagicMock()
        mock_db_result.scalar_one_or_none.return_value = mock_bp
        mock_db.execute.return_value = mock_db_result

        result = await get_blueprint_by_id(mock_db, "my-bp")

        assert result is not None
        assert result["id"] == "my-bp"

    @pytest.mark.asyncio
    async def test_get_blueprint_by_id_falls_back_to_first(self):
        """get_blueprint_by_id returns first fallback when ID not found in DB or fallbacks."""
        from src.services.nexus_engine.blueprints import get_blueprint_by_id, FALLBACK_BLUEPRINTS

        mock_db = AsyncMock()
        mock_db_result = MagicMock()
        mock_db_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_db_result

        result = await get_blueprint_by_id(mock_db, "nonexistent-blueprint-id")

        # Should return the first fallback (viral-reskin)
        assert result is not None
        assert result["id"] == "viral-reskin"

    @pytest.mark.asyncio
    async def test_get_blueprint_by_id_finds_fallback(self):
        """get_blueprint_by_id finds the matching fallback blueprint by ID."""
        from src.services.nexus_engine.blueprints import get_blueprint_by_id

        mock_db = AsyncMock()
        mock_db_result = MagicMock()
        mock_db_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_db_result

        result = await get_blueprint_by_id(mock_db, "topic-fusion")

        assert result is not None
        assert result["id"] == "topic-fusion"
        assert result["name"] == "Topic Narrative Fusion"
