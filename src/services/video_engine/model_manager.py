import logging
import asyncio
import shutil
import importlib.util
from pathlib import Path

from src.api.config import settings


def check_module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


class ModelManager:
    """
    Handles downloading and deleting large video models to save space on the VPS.
    """

    def __init__(self):
        self.models_dir = Path(settings.COMFYUI_MODELS_DIR)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        # Persistent models stay on disk
        self.persistent_models = ["cogvideox-5b"]
        # Track active tasks using each model
        self.active_usage = {}  # {model_name: count}

    async def acquire_model(self, model_name: str) -> str:
        """
        Increments usage counter and ensures model is present.
        Downloads from HuggingFace if not available locally.
        """
        self.active_usage[model_name] = self.active_usage.get(model_name, 0) + 1
        model_path = self.models_dir / f"{model_name}.safetensors"

        if model_path.exists():
            logging.info(
                f"[ModelManager] Acquired {model_name} (Active users: {self.active_usage[model_name]})"
            )
            return str(model_path)

        logging.info(f"[ModelManager] Downloading model: {model_name}...")

        try:
            # Download from HuggingFace
            await self._download_model_from_hf(model_name, model_path)
            logging.info(f"[ModelManager] Download complete: {model_name}")
        except Exception as e:
            logging.exception(f"[ModelManager] Download failed for {model_name}: {e}")
            # Fallback to touch (for testing)
            model_path.touch()
            logging.warning(f"[ModelManager] Using mock model for {model_name}")

        return str(model_path)

    async def _download_model_from_hf(self, model_name: str, target_path: Path):
        """
        Download model from HuggingFace Hub.
        """
        if not check_module_available("huggingface_hub"):
            logging.warning(
                "[ModelManager] huggingface_hub not installed, skipping real download"
            )
            raise RuntimeError("huggingface_hub not available")

        from huggingface_hub import hf_hub_download

        # Map model names to HuggingFace repo/file paths
        model_mapping = {
            "cogvideox-5b": ("THUDM/CogVideoX-5B", "CogVideoX-5B-I2V-5B.safetensors"),
            "hunyuan": ("Tencent/HunyuanVideo", "HunyuanVideo.safetensors"),
            "wan": ("Wan-AI/Wan2.2-T2V-14B", "Wan2.2-T2V-14B.safetensors"),
        }

        if model_name not in model_mapping:
            raise ValueError(f"Unknown model: {model_name}")

        repo_id, filename = model_mapping[model_name]

        # Download in background thread to avoid blocking
        import concurrent.futures

        def download_sync():
            return hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=str(self.models_dir),
                local_dir_use_symlinks=False,
            )

        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            downloaded_path = await loop.run_in_executor(executor, download_sync)

        # Move to expected location
        if downloaded_path != str(target_path):
            await asyncio.to_thread(shutil.move, downloaded_path, str(target_path))

    async def release_model(self, model_name: str):
        """
        Decrements usage counter and only cleans up if no other tasks need it.
        """
        if model_name not in self.active_usage:
            return

        self.active_usage[model_name] -= 1
        count = self.active_usage[model_name]

        logging.info(
            f"[ModelManager] Released {model_name} (Active users remaining: {count})"
        )

        if count <= 0:
            if (
                model_name in self.persistent_models
                or not settings.CLEANUP_TRANSIENT_MODELS
            ):
                logging.info(f"[ModelManager] Skipping cleanup for {model_name}")
            else:
                model_path = self.models_dir / f"{model_name}.safetensors"
                if model_path.exists():
                    logging.info(
                        f"[ModelManager] No more users. Cleaning up transient model: {model_name}"
                    )
                    await asyncio.to_thread(model_path.unlink)

            if model_name in self.active_usage:
                del self.active_usage[model_name]
