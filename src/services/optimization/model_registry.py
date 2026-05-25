import os
import json
import time
import shutil
import logging

logger = logging.getLogger("ModelRegistry")

class ModelRegistry:
    """
    10/10 Governance: Manages the lifecycle of Neural Oracle weights.
    Supports versioning, performance history, and zero-downtime hot-swaps.
    """
    def __init__(self, registry_dir: str = "data/models"):
        self.registry_dir = registry_dir
        self.registry_file = os.path.join(registry_dir, "registry.json")
        os.makedirs(self.registry_dir, exist_ok=True)
        self._ensure_registry_exists()

    def _ensure_registry_exists(self):
        if not os.path.exists(self.registry_file):
            with open(self.registry_file, "w") as f:
                json.dump({
                    "champion": "v1.0.0_bootstrap",
                    "versions": {
                        "v1.0.0_bootstrap": {
                            "created_at": time.time(),
                            "mae": 0.12,
                            "training_samples": 0,
                            "path": "oracle_v1_bootstrap.pth",
                            "status": "deployed"
                        }
                    }
                }, f, indent=4)

    def register_new_version(self, version_id: str, weights_path: str, mae: float, samples: int) -> bool:
        """Registers a new challenger model version."""
        try:
            with open(self.registry_file, "r") as f:
                data = json.load(f)

            dest_path = os.path.join(self.registry_dir, f"{version_id}.pth")
            shutil.copy(weights_path, dest_path)

            data["versions"][version_id] = {
                "created_at": time.time(),
                "mae": mae,
                "training_samples": samples,
                "path": f"{version_id}.pth",
                "status": "shadow"
            }

            with open(self.registry_file, "w") as f:
                json.dump(data, f, indent=4)
            
            logger.info(f"[Registry] Registered new version: {version_id} (MAE: {mae})")
            return True
        except Exception as e:
            logger.exception(f"[Registry] Failed to register version {version_id}: {e}")
            return False

    def promote_to_champion(self, version_id: str):
        """Promotes a version to the active 'Champion' model."""
        with open(self.registry_file, "r") as f:
            data = json.load(f)

        if version_id not in data["versions"]:
            logger.error(f"[Registry] Version {version_id} not found.")
            return

        old_champion = data["champion"]
        if old_champion in data["versions"]:
            data["versions"][old_champion]["status"] = "archived"

        data["champion"] = version_id
        data["versions"][version_id]["status"] = "deployed"

        with open(self.registry_file, "w") as f:
            json.dump(data, f, indent=4)
        
        logger.info(f"[Registry] PROMOTED {version_id} to CHAMPION. Old champion {old_champion} archived.")

    def get_champion_path(self) -> str:
        """Returns the filesystem path to the current active weights."""
        with open(self.registry_file, "r") as f:
            data = json.load(f)
        version = data["versions"][data["champion"]]
        return os.path.join(self.registry_dir, version["path"])

base_registry_service = ModelRegistry()
