import json
import logging
import time
import numpy as np
from typing import Any
from src.services.optimization.oracle_predictor import base_oracle_service
from src.services.infrastructure.event_bus import base_event_service
from src.services.optimization.model_registry import base_registry_service

logger = logging.getLogger("InferenceGateway")

class InferenceGateway:
    """
    10/10 Scalability: The Unified Entry Point for Distributed Intelligence.
    Decouples the 'Brain' (Inference) from the 'Body' (API/Jobs).
    """
    def __init__(self):
        self.oracle = base_oracle_service
        self.bus = base_event_service
        self.registry = base_registry_service

    async def predict_retention(self, numerical_features: list[float], clip_embedding: np.ndarray | None = None) -> np.ndarray:
        """
        Request a prediction from the Neural Oracle.
        In a multi-node setup, this could be an RPC call or an event on the bus.
        Currently: Local-first with distributed logging.
        """
        # Emit an 'Inference Requested' event for metrics
        await self.bus.emit("VF_INFERENCE_REQ", {
            "model_version": self.registry.get_champion_path().split("/")[-1],
            "feature_dim": len(numerical_features)
        })

        return self.oracle.predict_curve(numerical_features, clip_embedding)

    async def hot_swap_model(self, version_id: str):
        """Orchestrates a cluster-wide model update."""
        logger.warning(f"🚨 [Gateway] Orchestrating cluster-wide swap to {version_id}")

        # 1. Update local registry champion
        self.registry.promote_to_champion(version_id)

        # 2. Reload local oracle
        self.oracle.reload_champion()

        # 3. Broadcast to cluster
        await self.bus.emit("VF_HOT_SWAP_SIGNAL", {
            "new_version": version_id,
            "target": "ALL_NODES"
        })

    def get_system_vitals(self) -> dict[str, Any]:
        """Returns the vitals of the distributed intelligence layer."""
        with open(self.registry.registry_file, "r") as f:
            data = json.load(f)

        champion_data = data["versions"][data["champion"]]

        return {
            "model_version": data["champion"],
            "model_mae": champion_data["mae"],
            "model_status": champion_data["status"],
            "bus_status": "CONNECTED" if self.bus else "DISCONNECTED",
            "uptime_seconds": time.time() - champion_data["created_at"]
        }

base_inference_service = InferenceGateway()
