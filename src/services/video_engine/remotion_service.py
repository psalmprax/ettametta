import os
import json
import asyncio
import logging
import uuid
import shutil
import tempfile
import sys
import stat
from pathlib import Path
from typing import Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.api.config import settings
from src.api.utils.resilience import CircuitBreaker

logger = logging.getLogger(__name__)


class RemotionError(Exception):
    """Base exception for Remotion rendering service errors."""
    pass


class RemotionFatalError(RemotionError):
    """Fatal error indicating malformed input, missing assets, or invalid schema that cannot be retried."""
    pass


class RemotionTransientError(RemotionError):
    """Transient error indicating external timeouts, Chromium resource exhaustion, or transient process crashes."""
    pass


class JobIdAdapter(logging.LoggerAdapter):
    """Prefixes log messages with [Job ID] if present in extra context."""
    def process(self, msg: str, kwargs: Any) -> tuple[str, Any]:
        job_id = (self.extra or {}).get("job_id")
        prefix = f"[{job_id}] " if job_id else ""
        return f"{prefix}{msg}", kwargs


class RemotionService:
    """
    Bridges Python logic to the Remotion React studio for programmatic video rendering.
    Hardened with Circuit Breaker, isolated asset staging sandboxes, and structured validation.
    Protects CPU/RAM via asyncio Semaphore concurrency guarding.
    Uses non-blocking asyncio subprocess for production scale.
    """

    def __init__(self, studio_path: str | None = None, concurrency_limit: int | None = None):
        self.studio_path = os.path.abspath(studio_path or settings.REMOTION_STUDIO_PATH)
        self.output_dir = os.path.join(self.studio_path, "out")
        os.makedirs(self.output_dir, exist_ok=True)
        
        limit = concurrency_limit if concurrency_limit is not None else settings.REMOTION_CONCURRENCY_LIMIT
        # Concurrency guarding to prevent event loop starvation and server crashes
        self.render_semaphore = asyncio.Semaphore(limit)
        
        # Cache baseline context logger to avoid duplicate adapter instantiation overhead in initialization
        self._default_log = self._get_logger()
        self._default_log.info(f"[RemotionService] Initialized with concurrency limit: {limit}")

        # Dynamic browser discovery
        self.browser_path = os.getenv("CHROMIUM_PATH") or \
                           shutil.which("chromium") or \
                           shutil.which("chromium-browser")
        
        if self.browser_path:
            self._default_log.info(f"[RemotionService] Using browser at: {self.browser_path}")
        else:
            self._default_log.warning("[RemotionService] No browser found in PATH. Remotion will attempt auto-download.")
        
        self.breaker = CircuitBreaker(name="RemotionRender", failure_threshold=2, recovery_timeout=300)

        # Strict allowed staging roots jail to prevent Local File Inclusion (LFI)
        # Sanitized with the single source of truth path normalizer
        self.allowed_roots = [
            self._normalize_and_resolve_path(self.studio_path),
            self._normalize_and_resolve_path(os.path.join(self.studio_path, "public")),
            self._normalize_and_resolve_path(getattr(settings, "OUTPUT_DIR", None) or "/app/outputs"),
            self._normalize_and_resolve_path(tempfile.gettempdir()),
            self._normalize_and_resolve_path("/app/temp"),
            self._normalize_and_resolve_path("/app/downloads"),
            self._normalize_and_resolve_path("/app/local_downloads"),
            self._normalize_and_resolve_path("local_downloads"),
        ]
        
        # Initialize Prometheus circuit breaker state
        self._update_breaker_metrics()

    def _get_logger(self, job_id: str | None = None) -> logging.LoggerAdapter:
        """Retrieve a logger adapter prefixed with the active job_id."""
        return JobIdAdapter(logger, {"job_id": job_id})

    def _normalize_and_resolve_path(self, path: str | Path) -> str:
        """
        Robust single-source-of-truth helper to resolve and normalize paths.
        Handles symlinks, mixed separators, and absolute resolution.
        """
        try:
            p = Path(path).resolve().absolute()
            return str(p)
        except Exception as e:
            self._default_log.debug(f"Pathlib resolution failed for {path}, falling back to abspath/realpath: {e}")
            return os.path.realpath(os.path.abspath(path))

    def _update_breaker_metrics(self) -> None:
        """Update the Prometheus circuit breaker state gauge."""
        try:
            from src.services.infrastructure.resilience_metrics import remotion_circuit_breaker_state
            state_map = {"CLOSED": 0, "HALF_OPEN": 1, "OPEN": 2}
            val = state_map.get(self.breaker.state, 0)
            remotion_circuit_breaker_state.set(val)
        except Exception as e:
            self._default_log.debug(f"Failed to update circuit breaker metrics: {e}")

    def _breaker_record_success(self) -> None:
        """Record success on circuit breaker and atomically sync Prometheus gauge."""
        self.breaker.record_success()
        self._update_breaker_metrics()

    def _breaker_record_failure(self) -> None:
        """Record failure on circuit breaker and atomically sync Prometheus gauge."""
        self.breaker.record_failure()
        self._update_breaker_metrics()

    def _get_approx_memory_size(self, obj: Any, current_size: int = 0, limit: int = 50 * 1024 * 1024, seen: set[int] | None = None) -> int:
        """Recursively estimates memory size of input objects synchronously to prevent DOS payload attacks, with cyclic reference tracking."""
        if seen is None:
            seen = set()
            
        oid = id(obj)
        if oid in seen:
            return current_size
            
        seen.add(oid)
        
        size = sys.getsizeof(obj)
        total = current_size + size
        if total > limit:
            raise RemotionFatalError(f"Props memory footprint exceeded maximum allowed limit of {limit} bytes")
        
        if isinstance(obj, dict):
            for k, v in obj.items():
                total = self._get_approx_memory_size(k, total, limit, seen)
                total = self._get_approx_memory_size(v, total, limit, seen)
        elif isinstance(obj, (list, tuple, set)):
            for item in obj:
                total = self._get_approx_memory_size(item, total, limit, seen)
        return total

    def _validate_props(self, composition_id: str, props: dict[str, Any]) -> None:
        """
        Fast-fail structured validation checks on rendering parameters to prevent wasting resources.
        Synchronous and CPU-light to prevent unnecessary await context-switching overhead.
        """
        if not composition_id or not isinstance(composition_id, str):
            raise RemotionFatalError("composition_id must be a valid non-empty string.")
            
        if not isinstance(props, dict):
            raise RemotionFatalError("Props must be a dictionary.")

        # Enforce synchronous, non-blocking recursive memory footprint guard (50MB ceiling) to block memory injection DOS
        self._get_approx_memory_size(props)
        
        if "duration_in_frames" in props:
            try:
                frames = int(props["duration_in_frames"])
                if frames <= 0:
                    raise RemotionFatalError(f"duration_in_frames must be a positive integer, got: {frames}")
            except (ValueError, TypeError):
                raise RemotionFatalError(f"duration_in_frames must be a valid integer, got: {props['duration_in_frames']}")

    def _prepare_job_assets(self, props: dict[str, Any], job_id: str, log: logging.LoggerAdapter) -> tuple[dict[str, Any], str]:
        """
        Recursively scans props for local absolute file paths or temp/output directory paths,
        safely stages them in a job-isolated directory (`public/assets/{job_id}/`),
        and returns the modified relative-pathed props dictionary along with the job assets directory path.
        """
        # Define the job-scoped public assets sandbox to avoid concurrent race conditions
        job_assets_dir = os.path.join(self.studio_path, "public", "assets", job_id)
        os.makedirs(job_assets_dir, exist_ok=True)

        remotion_ready_props = self._recursive_prep_assets(props, job_assets_dir, job_id, log)
        return remotion_ready_props, job_assets_dir

    def _prepare_single_asset(self, src_path: str, job_assets_dir: str, job_id: str, log: logging.LoggerAdapter) -> str:
        """
        Validates a local file path, checks containment/LFI, and copies it to the job sandbox.
        Returns the browser-compatible relative path or the original string if invalid/not allowed.
        """
        if not src_path or src_path.startswith("http") or src_path.startswith("assets/"):
            return src_path

        try:
            # 1. Resolve and normalize absolute path using the single-source-of-truth helper
            src_real = self._normalize_and_resolve_path(src_path)
            src_p = Path(src_real)

            # Suffix validation check on resolved path
            if not src_p.suffix:
                return src_path

            # Explicit check to reject symlink files at the raw path level before kernel-opening
            if Path(src_path).is_symlink():
                log.warning(f"[LFI Guard] Blocked raw symlink asset path: {src_path}")
                return src_path

            # Airtight, race-proof LFI mitigation: open the target file with O_NOFOLLOW to block symlinks at kernel level.
            # This completely eliminates Time-of-Check to Time-of-Use (TOCTOU) file-swap race conditions.
            try:
                fd = os.open(src_real, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            except OSError as e:
                log.warning(f"[LFI Guard] Blocked symbolic link or invalid file access: {src_path} ({e})")
                return src_path

            try:
                # Retrieve fstat to perform regular file type validation under the OS lock
                st = os.fstat(fd)
                if not stat.S_ISREG(st.st_mode):
                    log.warning(f"[LFI Guard] Rejected non-regular file: {src_path}")
                    return src_path

                # Once we have the open fd, it is locked at OS level to a specific inode.
                # Check path containment securely against permitted directories
                is_allowed = False
                for root in self.allowed_roots:
                    root_p = Path(root)
                    try:
                        src_p.relative_to(root_p)
                        is_allowed = True
                        break
                    except ValueError:
                        pass

                if not is_allowed:
                    log.warning(f"[LFI Guard] Blocked copying asset outside allowed staging roots: {src_path}")
                    return src_path

                # 4. Copy via locked file descriptor
                uuid_prefix = uuid.uuid4().hex[:8]
                filename = f"{uuid_prefix}_{src_p.name}"
                dest_path = os.path.join(job_assets_dir, filename)

                # Avoid copying a file to itself if it's already in the destination
                if src_real != self._normalize_and_resolve_path(dest_path):
                    with open(fd, "rb", closefd=False) as f_in:
                        with open(dest_path, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    log.info(f"Prepared physical asset: {filename} in sandbox {job_id}")
                
                return f"assets/{job_id}/{filename}"
            finally:
                os.close(fd)
        except Exception:
            log.exception(f"Failed to copy physical asset {src_path}")
            return src_path

    def _recursive_prep_assets(self, obj: Any, job_assets_dir: str, job_id: str, log: logging.LoggerAdapter) -> Any:
        """
        Recursively prep assets for Remotion, moving local files to the job sandbox.
        """
        if isinstance(obj, dict):
            return {k: self._recursive_prep_assets(v, job_assets_dir, job_id, log) for k, v in obj.items()}
        
        if isinstance(obj, list):
            return [self._recursive_prep_assets(i, job_assets_dir, job_id, log) for i in obj]
        
        if isinstance(obj, str):
            return self._stage_string_asset(obj, job_assets_dir, job_id, log)
            
        return obj

    def _stage_string_asset(self, val: str, job_assets_dir: str, job_id: str, log: logging.LoggerAdapter) -> str:
        """
        Entrypoint for string staging. Passes the string to _prepare_single_asset
        if it might represent a file path.
        """
        if not val or val.startswith("http") or val.startswith("assets/"):
            return val
        
        # Quick pre-filter to avoid resolving strings that clearly aren't paths
        if "/" not in val and "\\" not in val and not os.path.isabs(val):
            return val

        return self._prepare_single_asset(val, job_assets_dir, job_id, log)

    def _check_disk_space(self, parent_dir: str, required_space: int, log: logging.LoggerAdapter) -> None:
        """Helper to verify disk space is sufficient before writing."""
        try:
            usage = shutil.disk_usage(parent_dir)
            if usage.free < required_space:
                raise IOError(f"Insufficient disk space in {parent_dir}. Free: {usage.free} bytes, Required: {required_space} bytes")
        except IOError:
            raise
        except Exception as e:
            log.debug(f"Could not verify disk usage for {parent_dir}: {e}")

    def _try_write_props_once(self, tmp_path: str, path: str, serialized_bytes: bytes) -> None:
        """Write serialized bytes to a temp file, flush/fsync, and atomically replace the destination."""
        with open(tmp_path, "wb") as f:
            f.write(serialized_bytes)
            f.flush()
            os.fsync(f.fileno())
        
        os.replace(tmp_path, path)

    def _safe_remove_tmp_file(self, tmp_path: str) -> None:
        """Safely delete the temp file if it exists, ignoring exceptions."""
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def _write_props_file(self, path: str, props: dict[str, Any], log: logging.LoggerAdapter) -> None:
        """Helper to serialize props to disk atomically with disk checks and retries. Executed in a background thread."""
        try:
            serialized_props = json.dumps(props, ensure_ascii=False)
            serialized_bytes = serialized_props.encode("utf-8")
        except (TypeError, ValueError) as e:
            raise RemotionFatalError(f"Props must be JSON serializable: {e}")
            
        byte_size = len(serialized_bytes)
        if byte_size > 10 * 1024 * 1024:
            raise RemotionFatalError(f"Props serialized size is too large: {byte_size} bytes (max allowed is 10MB)")

        tmp_path = f"{path}.tmp"
        parent_dir = os.path.dirname(os.path.abspath(path))
        required_space = max(20 * 1024 * 1024, byte_size * 2)  # 20MB or 2x payload bytes
        
        self._check_disk_space(parent_dir, required_space, log)

        # Write with local retries (2 attempts) to handle transient file lock conditions without stacked latency amplification
        import time
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                self._try_write_props_once(tmp_path, path, serialized_bytes)
                return  # Success!
            except Exception:
                self._safe_remove_tmp_file(tmp_path)
                if attempt == max_attempts - 1:
                    log.exception(f"Failed to write props file after {max_attempts} attempts")
                    raise
                time.sleep(0.1 * (attempt + 1))

    def _get_remotion_executable(self) -> tuple[str, list[str]]:
        """Determine base Remotion executable and initial arguments."""
        local_bin = os.path.join(self.studio_path, "node_modules", ".bin", "remotion")
        if os.path.exists(local_bin):
            return local_bin, []
        return "npx", ["remotion"]

    def _wrap_with_nice(self, program_base: str, args_base: list[str]) -> tuple[str, list[str]]:
        """Wrap the Remotion execution with 'nice' priority adjustment if available."""
        if shutil.which("nice"):
            return "nice", ["-n", "10", program_base] + args_base
        return program_base, args_base

    def _get_duration_frames_arg(self, props: dict[str, Any], log: logging.LoggerAdapter) -> list[str]:
        """Extract frame duration arguments safely from props."""
        if "duration_in_frames" not in props:
            return []
        
        try:
            frames_val = int(props["duration_in_frames"])
            return ["--frames", f"0-{frames_val}"]
        except (ValueError, TypeError) as e:
            log.warning(f"Invalid duration_in_frames found during render command build: {e}")
            return []

    def _get_cgroup_memory_limit(self) -> int | None:
        """Attempts to read the container memory limit from cgroups (v1 or v2)."""
        # Cgroups v2
        if os.path.exists("/sys/fs/cgroup/memory.max"):
            try:
                with open("/sys/fs/cgroup/memory.max", "r") as f:
                    val = f.read().strip()
                    if val and val != "max":
                        return int(val)
            except Exception:
                pass

        # Cgroups v1
        if os.path.exists("/sys/fs/cgroup/memory/memory.limit_in_bytes"):
            try:
                with open("/sys/fs/cgroup/memory/memory.limit_in_bytes", "r") as f:
                    val = f.read().strip()
                    if val:
                        limit = int(val)
                        if limit < 9000000000000000000:
                            return limit
            except Exception:
                pass

        return None

    def _get_dynamic_max_old_space_size(self) -> int:
        """Gets memory limit in MB dynamically, scaling to host/container constraints."""
        limit_bytes = self._get_cgroup_memory_limit()
        
        # Fallback to system memory (/proc/meminfo) if cgroups info is missing or unlimited
        if not limit_bytes or limit_bytes <= 0:
            try:
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            parts = line.split()
                            if len(parts) >= 2:
                                limit_bytes = int(parts[1]) * 1024  # kB to bytes
                                break
            except Exception:
                pass

        # Global fallback: default to 4GB
        if not limit_bytes or limit_bytes <= 0:
            limit_bytes = 4 * 1024 * 1024 * 1024

        limit_mb = limit_bytes // (1024 * 1024)
        # Allocate ~60% of available memory to V8, clamped between 1024MB and 8192MB
        return max(1024, min(8192, int(limit_mb * 0.6)))

    def _build_render_command(self, composition_id: str, props: dict[str, Any], output_path: str, props_path: str, output_name: str, log: logging.LoggerAdapter) -> tuple[str, list[str]]:
        """
        Safely builds the executable program and argument array for Remotion rendering.
        """
        program_base, args_base = self._get_remotion_executable()
        program, args = self._wrap_with_nice(program_base, args_base)

        args.extend([
            "render",
            "src/index.ts",
            composition_id,
            output_path,
            "--props", props_path,
        ])

        if self.browser_path:
            args.extend(["--browser-executable", self.browser_path])

        args.extend(["--concurrency", "1"])

        args.extend(self._get_duration_frames_arg(props, log))

        # Dynamically allocate memory for node/chromium process
        limit_mb = self._get_dynamic_max_old_space_size()
        log.info(f"[RemotionService] Dynamic max-old-space-size calculated: {limit_mb}MB")

        # Harden chromium flags by removing unstable/dangerous '--single-process' and '--disable-web-security'
        chrome_flags = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            f"--js-flags='--max-old-space-size={limit_mb}'"
        ]
        
        scale_val = "0.5" if "test" in (output_name or "") else "1"
        
        args.extend([
            "--chromium-flags", " ".join(chrome_flags),
            "--public-dir=public",
            "--scale", scale_val,
            "--force"
        ])

        return program, args

    async def _drain_stdout(self, stream: asyncio.StreamReader, log: logging.LoggerAdapter) -> None:
        """Helper to drain subprocess stdout and log rendering progress."""
        try:
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode("utf-8", errors="ignore").strip()
                if decoded and ("Rendered" in decoded or "Frame" in decoded or "%" in decoded):
                    log.debug(f"[Remotion stdout] {decoded}")
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("Error draining stdout")

    async def _drain_stderr(self, stream: asyncio.StreamReader, stderr_accumulator: list[str], log: logging.LoggerAdapter) -> None:
        """Helper to drain subprocess stderr and accumulate error logs."""
        try:
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode("utf-8", errors="ignore").strip()
                if decoded:
                    log.warning(f"[Remotion stderr] {decoded}")
                    stderr_accumulator.append(decoded)
                    if len(stderr_accumulator) > 100:
                        stderr_accumulator.pop(0)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("Error draining stderr")

    async def _terminate_process(self, process: asyncio.subprocess.Process, log: logging.LoggerAdapter) -> None:
        """Helper to aggressively terminate a process during cancellation."""
        try:
            process.kill()
            await process.wait()
        except ProcessLookupError:
            pass  # Process already exited; nothing to clean up
        except OSError:
            log.warning("OS error while killing cancelled process")

    def _check_process_returncode(self, returncode: int, stderr_accumulator: list[str], log: logging.LoggerAdapter) -> None:
        """Helper to raise an error if the subprocess failed."""
        if returncode == 0:
            log.info("Subprocess render completed successfully.")
            return

        error_msg = "\n".join(stderr_accumulator)[-2000:] if stderr_accumulator else "Unknown CLI render error"
        log.error(f"Remotion CLI failed (exit code {returncode}): {error_msg}")
        raise RemotionTransientError(f"Remotion CLI failed with exit code {returncode}: {error_msg}")

    async def _execute_render(self, program: str, args: list[str], log: logging.LoggerAdapter) -> None:
        """
        Launches the asynchronous subprocess, monitors execution, and enforces timeout limits.
        """
        trimmed_args = [a[:100] + "..." if len(a) > 100 else a for a in args]
        log.info(f"Executing: {program} {' '.join(trimmed_args)}")
        
        process = await asyncio.create_subprocess_exec(
            program,
            *args,
            cwd=self.studio_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stderr_accumulator: list[str] = []
        stdout_task = asyncio.create_task(self._drain_stdout(process.stdout, log))
        stderr_task = asyncio.create_task(self._drain_stderr(process.stderr, stderr_accumulator, log))

        # Decouple rendering timeout from LLM configuration parameters
        timeout = getattr(settings, "REMOTION_TIMEOUT_SECONDS", 900)

        try:
            async with asyncio.timeout(timeout):
                await asyncio.gather(stdout_task, stderr_task, process.wait())
            self._check_process_returncode(process.returncode, stderr_accumulator, log)
        except (TimeoutError, asyncio.CancelledError) as e:
            # Request cancellation of the stdout/stderr stream readers
            stdout_task.cancel()
            stderr_task.cancel()
            
            # Await stream tasks with return_exceptions=True to clean them up and suppress warnings
            await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)
            
            # Unconditionally terminate the process to guarantee zero process leakage
            await self._terminate_process(process, log)
            
            if isinstance(e, TimeoutError):
                log.error(f"Subprocess render timed out after {timeout} seconds.")
                raise RemotionTransientError(f"Remotion CLI render timed out after {timeout} seconds.") from e
            else:
                log.error("Rendering process was cancelled.")
                raise

    def _cleanup_job(self, props_path: str, job_assets_dir: str | None, log: logging.LoggerAdapter) -> None:
        """
        Cleans up transient json files and sandboxed asset subdirectories safely,
        with detailed warning logs for non-blocking file handling issues.
        """
        for path in [props_path, f"{props_path}.tmp"]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                    log.debug(f"Cleaned up props file: {path}")
                except Exception:
                    log.exception(f"Failed to clean up props file {path}")

        if job_assets_dir and os.path.exists(job_assets_dir):
            try:
                shutil.rmtree(job_assets_dir)
                log.debug(f"Cleaned up isolated job sandbox: {job_assets_dir}")
            except Exception:
                log.exception(f"Failed to clean up assets sandbox {job_assets_dir}")

    def _record_render_metrics(self, composition_id: str, status: str, duration: float | None = None) -> None:
        """Helper to safely record rendering telemetry to Prometheus metrics without duplication."""
        try:
            from src.services.infrastructure.resilience_metrics import remotion_renders, remotion_render_duration
            if remotion_renders:
                remotion_renders.labels(composition_id=composition_id, status=status).inc()
            if duration is not None and remotion_render_duration:
                remotion_render_duration.labels(composition_id=composition_id).observe(duration)
        except Exception as e:
            self._default_log.debug(f"Failed to record Prometheus metrics: {e}")

    def _verify_render_output(self, output_path: str, log: logging.LoggerAdapter) -> None:
        """Verify output file existence and non-zero size."""
        if not os.path.exists(output_path):
            log.error(f"Render output file is missing: {output_path}")
            raise RemotionTransientError(f"Render completed but output file is missing: {output_path}")
        
        file_size = os.path.getsize(output_path)
        if file_size == 0:
            log.error(f"Render output file is empty: {output_path}")
            raise RemotionTransientError(f"Render completed but output file is empty (0 bytes): {output_path}")

    def _pre_render_checks(self, composition_id: str, props: dict[str, Any], log: logging.LoggerAdapter) -> None:
        """Perform fast pre-render checks, validating the circuit breaker and props."""
        if self.breaker.is_open():
            log.error("Circuit breaker is OPEN. Rendering denied.")
            self._record_render_metrics(composition_id, "transient_failure")
            raise RemotionTransientError("Remotion rendering service is temporarily unavailable (Circuit OPEN)")

        # Always update Prometheus metrics on state checks to prevent gauge drift (captures half-open state recovery)
        self._update_breaker_metrics()

        try:
            self._validate_props(composition_id, props)
        except RemotionFatalError as e:
            self._record_render_metrics(composition_id, "fatal_failure")
            raise e

    @retry(
        stop=stop_after_attempt(2), 
        wait=wait_exponential(multiplier=2, min=10, max=60),
        retry=retry_if_exception_type(RemotionTransientError),
        reraise=True
    )
    async def render_video(self, composition_id: str, props: dict[str, Any], output_name: str = None) -> str | None:
        """
        Main entrypoint orchestrating pre-validation, sandboxed asset preparation, 
        non-blocking config generation, event-loop-safe subprocess supervisor, 
        and full garbage collection.
        
        Protected by self.render_semaphore to guarantee hardware concurrency safety,
        and `@retry` only on transient (non-deterministic) network/timeout failures.
        """
        job_id = str(uuid.uuid4())[:8]
        log = self._get_logger(job_id)

        self._pre_render_checks(composition_id, props, log)

        if not output_name:
            output_name = f"render_{job_id}.mp4"
        
        output_path = os.path.join(self.output_dir, output_name)
        input_props_path = os.path.join(self.studio_path, f"props_{job_id}.json")
        job_assets_dir = None

        # Concurrency queue gate
        async with self.render_semaphore:
            log.info(f"Acquired render slot for job {job_id} ({composition_id})")
            start_time = asyncio.get_running_loop().time()
            
            try:
                # Safe isolated asset preparation (no file race conditions)
                remotion_ready_props, job_assets_dir = self._prepare_job_assets(props, job_id, log)

                # Offloaded JSON write (non-blocking) with disk space check, size limits, and retry wrapper
                await asyncio.to_thread(self._write_props_file, input_props_path, remotion_ready_props, log)

                # Build render CLI command cleanly
                program, args = self._build_render_command(
                    composition_id, remotion_ready_props, output_path, input_props_path, output_name, log
                )

                # Execute non-blocking process monitor with internal timeout guarding and stream cleanup
                await self._execute_render(program, args, log)
                
                # Post-Render Output Validation
                self._verify_render_output(output_path, log)
                
                duration = asyncio.get_running_loop().time() - start_time
                log.info(f"[Telemetry] Render job completed successfully in {duration:.2f} seconds. Size: {os.path.getsize(output_path)} bytes")
                
                # Record metrics
                self._record_render_metrics(composition_id, "success", duration)
                
                # Consolidate circuit breaker success mutator
                self._breaker_record_success()
                return output_path

            except RemotionFatalError:
                duration = asyncio.get_running_loop().time() - start_time
                log.error(f"[Telemetry] Render job failed fatally in {duration:.2f} seconds.")
                self._record_render_metrics(composition_id, "fatal_failure")
                raise
            except RemotionTransientError:
                self._breaker_record_failure()
                duration = asyncio.get_running_loop().time() - start_time
                log.error(f"[Telemetry] Render job failed transiently in {duration:.2f} seconds.")
                self._record_render_metrics(composition_id, "transient_failure")
                raise
            except asyncio.CancelledError:
                duration = asyncio.get_running_loop().time() - start_time
                log.warning(f"[Telemetry] Render job was cancelled after {duration:.2f} seconds.")
                self._record_render_metrics(composition_id, "cancelled")
                raise
            except Exception as e:
                self._breaker_record_failure()
                duration = asyncio.get_running_loop().time() - start_time
                log.exception(f"[Telemetry] Unhandled system error during render for job {job_id} after {duration:.2f} seconds")
                self._record_render_metrics(composition_id, "transient_failure")
                raise RemotionTransientError(f"Unhandled render system crash: {e}") from e
            finally:
                self._cleanup_job(input_props_path, job_assets_dir, log)


base_remotion_service = RemotionService()
