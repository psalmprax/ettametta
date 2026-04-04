"""
AI Job Orchestrator - Smart Batching and VRAM Optimization
"""

import threading
import time
import uuid
import traceback
from typing import List, Dict, Any, Optional
from video_model_manager import model_manager
import ai_actions

class AIJob:
    def __init__(self, job_type: str, model_key: str, data: Any, job_id: str):
        self.job_id = job_id
        self.job_type = job_type # 'video', 'voice', 'vlm', 'transcribe'
        self.model_key = model_key # 'ltx_2_19b', 'whisper', 'tts', etc.
        self.data = data
        self.status = "queued"
        self.created_at = time.time()
        self.started_at = None
        self.completed_at = None
        self.error = None
        self.result = None
        self.jumps = 0 # How many times this job was "jumped" by others

class AIJobOrchestrator:
    def __init__(self):
        self.pending_jobs: List[AIJob] = []
        self.completed_jobs: Dict[str, AIJob] = {}
        self.lock = threading.Lock()
        self.max_jumps = 3 # Anti-starvation limit
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        print("🚀 AI Job Orchestrator initialized (Smart Batching enabled).", flush=True)

    def add_job(self, job_type: str, model_key: str, data: Any) -> str:
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        new_job = AIJob(job_type, model_key, data, job_id)
        with self.lock:
            self.pending_jobs.append(new_job)
            print(f"📥 [Orchestrator] Job {job_id} queued ({model_key})", flush=True)
        return job_id

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        with self.lock:
            # Check pending
            for i, job in enumerate(self.pending_jobs):
                if job.job_id == job_id:
                    return {
                        "job_id": job_id,
                        "status": "queued",
                        "position": i + 1,
                        "model": job.model_key,
                        "created_at": job.created_at
                    }
            # Check completed
            if job_id in self.completed_jobs:
                job = self.completed_jobs[job_id]
                return {
                    "job_id": job_id,
                    "status": job.status,
                    "result": job.result,
                    "error": job.error,
                    "completed_at": job.completed_at
                }
        return {"error": "Job not found"}

    def _worker_loop(self):
        while self.is_running:
            job_to_run = None
            
            with self.lock:
                if not self.pending_jobs:
                    time.sleep(1)
                    continue
                
                # --- SMART BATCHING LOGIC ---
                current_model = model_manager.current_model or (list(model_manager.utils.keys())[0] if model_manager.utils else None)
                
                best_idx = 0 # Default to FIFO
                
                if current_model:
                    # Check for model matches in queue to avoid VRAM swap
                    for i, job in enumerate(self.pending_jobs):
                        if job.model_key == current_model:
                            # Verify starvation
                            if self.pending_jobs[0].jumps < self.max_jumps:
                                best_idx = i
                                print(f"✨ [Batching] Promoting job {job.job_id} ({job.model_key}) to skip VRAM swap", flush=True)
                                break
                            else:
                                print(f"⚠️ [Batching] Starvation limit reached for {self.pending_jobs[0].job_id}. Forcing FIFO jump.", flush=True)
                                best_idx = 0
                                break
                
                # Increment jump counts for everyone we skipped
                for i in range(best_idx):
                    self.pending_jobs[i].jumps += 1

                job_to_run = self.pending_jobs.pop(best_idx)

            # --- EXECUTION ---
            if job_to_run:
                self._execute_job(job_to_run)

    def _execute_job(self, job: AIJob):
        print(f"🎬 [Orchestrator] Executing job {job.job_id} ({job.model_key})...", flush=True)
        job.status = "processing"
        job.started_at = time.time()
        
        try:
            if job.job_type == "video":
                job.result = ai_actions.action_render_video(job.job_id, job.model_key, job.data)
            elif job.job_type == "voice":
                job.result = ai_actions.action_generate_voice(job.data.text)
            elif job.job_type == "vlm":
                job.result = ai_actions.action_analyze_vlm(job.data.image_base64, job.data.prompt)
            elif job.job_type == "transcribe":
                job.result = ai_actions.action_transcription(job.data["file_path"])
            
            job.status = "completed"
        except Exception as e:
            print(f"❌ [Orchestrator] Job {job.job_id} failed: {e}", flush=True)
            traceback.print_exc()
            job.status = "failed"
            job.error = str(e)
        finally:
            job.completed_at = time.time()
            with self.lock:
                self.completed_jobs[job.job_id] = job
                
orchestrator = AIJobOrchestrator()
