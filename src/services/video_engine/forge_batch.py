"""
The Bulk Forge: Parallel Rendering Engine (10/10)
==============================================

Uses Python's multiprocessing to saturate CPU cores with 
parallel FFmpeg production variants for high-velocity scaling.
"""

import os
import logging
import concurrent.futures
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

class ForgeBatchRenderer:
    """
    High-Throughput Parallel Renderer for Final Productions.
    """
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers

    def _render_single_variant(self, variant_data: dict[str, Any]) -> dict[str, Any]:
        """Worker function for parallel variant rendering"""
        video_path = variant_data["output_path"]
        cmd = variant_data["cmd"]
        
        try:
            logger.info(f"🏗️  [ForgeBatch] Starting render: {video_path}")
            # Run FFmpeg command
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return {"success": True, "path": video_path, "variant_id": variant_data.get("variant_id")}
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ [ForgeBatch] Render Failed: {video_path}")
            logger.error(f"Error: {e.stderr}")
            return {"success": False, "error": e.stderr, "variant_id": variant_data.get("variant_id")}

    def render_batch(self, variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Parallelizes the rendering of multiple production variants"""
        results = []
        
        print(f"🚀 FORGE BATCH: Parallelizing {len(variants)} variants across {self.max_workers} cores...")
        
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_variant = {
                executor.submit(self._render_single_variant, v): v for v in variants
            }
            
            for future in concurrent.futures.as_completed(future_to_variant):
                results.append(future.result())
        
        success_count = sum(1 for r in results if r["success"])
        print(f"✅ FORGE BATCH COMPLETE: {success_count}/{len(variants)} successful renders.")
        return results

# Singleton Instance
base_forge_batch = ForgeBatchRenderer()
