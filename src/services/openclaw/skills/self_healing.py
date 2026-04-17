import psutil
import logging
import subprocess
import time
from datetime import datetime, timedelta
from .notifications import notification_skill
from .memory import memory_skill

logger = logging.getLogger(__name__)


class SelfHealingSkill:
    def __init__(self):
        self.monitored_processes: dict[str, dict] = {}
        self.health_checks: dict[str, dict] = {}
        self.auto_restart_enabled = True
        self.last_health_check = datetime.now()

    def monitor_process(
        self, name: str, command: str, health_check: callable = None
    ) -> str:
        """Start monitoring a process"""
        self.monitored_processes[name] = {
            "command": command,
            "health_check": health_check,
            "status": "starting",
            "pid": None,
            "start_time": datetime.now(),
            "restart_count": 0,
            "last_restart": None,
        }

        # Start the process
        try:
            process = subprocess.Popen(
                command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            self.monitored_processes[name]["pid"] = process.pid
            self.monitored_processes[name]["status"] = "running"
            logger.info(f"Started monitoring process '{name}' with PID {process.pid}")
            return f"✅ Started monitoring '{name}' (PID: {process.pid})"
        except Exception as e:
            self.monitored_processes[name]["status"] = "failed"
            logger.error(f"Failed to start process '{name}': {e}")
            return f"❌ Failed to start '{name}': {str(e)}"

    def check_process_health(self, name: str) -> dict:
        """Check health of a monitored process"""
        if name not in self.monitored_processes:
            return {"status": "not_monitored", "healthy": False}

        proc_info = self.monitored_processes[name]
        pid = proc_info["pid"]

        if not pid:
            return {"status": "no_pid", "healthy": False}

        try:
            process = psutil.Process(pid)
            if not process.is_running():
                return {"status": "not_running", "healthy": False}

            # Check CPU and memory usage
            cpu_percent = process.cpu_percent(interval=0.1)
            memory_percent = process.memory_percent()

            healthy = True
            issues = []

            if cpu_percent > 90:
                healthy = False
                issues.append(".1f")

            if memory_percent > 80:
                healthy = False
                issues.append(".1f")

            return {
                "status": "running",
                "healthy": healthy,
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "issues": issues,
            }

        except psutil.NoSuchProcess:
            return {"status": "process_gone", "healthy": False}
        except Exception as e:
            logger.error(f"Health check failed for '{name}': {e}")
            return {"status": "check_failed", "healthy": False, "error": str(e)}

    def restart_process(self, name: str) -> str:
        """Restart a monitored process"""
        if name not in self.monitored_processes:
            return f"❌ Process '{name}' not monitored"

        proc_info = self.monitored_processes[name]

        # Kill existing process
        if proc_info["pid"]:
            try:
                process = psutil.Process(proc_info["pid"])
                process.terminate()
                process.wait(timeout=5)
            except Exception as e:
                logger.warning(f"Failed to terminate '{name}': {e}")
                try:
                    process.kill()
                except:
                    pass

        # Restart
        try:
            process = subprocess.Popen(
                proc_info["command"].split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            proc_info["pid"] = process.pid
            proc_info["status"] = "running"
            proc_info["restart_count"] += 1
            proc_info["last_restart"] = datetime.now()

            memory_skill.record_event(
                "process_restart",
                {
                    "process": name,
                    "pid": process.pid,
                    "restart_count": proc_info["restart_count"],
                },
            )

            return f"✅ Restarted '{name}' (PID: {process.pid}, restarts: {proc_info['restart_count']})"
        except Exception as e:
            proc_info["status"] = "failed"
            return f"❌ Failed to restart '{name}': {str(e)}"

    def perform_health_check(self) -> str:
        """Perform health checks on all monitored processes"""
        self.last_health_check = datetime.now()
        results = []
        alerts = []

        for name in self.monitored_processes:
            health = self.check_process_health(name)
            status = health["status"]
            healthy = health["healthy"]

            if not healthy:
                alerts.append(f"⚠️ {name}: {status}")
                if self.auto_restart_enabled and status in [
                    "not_running",
                    "process_gone",
                ]:
                    restart_result = self.restart_process(name)
                    alerts.append(restart_result)

            results.append(f"• {name}: {status} ({'✅' if healthy else '❌'})")

        # Send alerts if any
        if alerts:
            alert_message = "**Health Check Alerts**\n" + "\n".join(alerts)
            notification_skill.send_notification("telegram", alert_message, "high")

        summary = (
            f"🏥 **Health Check Complete** ({len(results)} processes)\n"
            + "\n".join(results)
        )
        return summary

    def add_health_check(
        self, name: str, check_function: callable, interval_minutes: int = 5
    ) -> str:
        """Add a custom health check"""
        self.health_checks[name] = {
            "function": check_function,
            "interval_minutes": interval_minutes,
            "last_check": None,
            "status": "configured",
        }
        return f"✅ Added health check '{name}' (every {interval_minutes} minutes)"

    def run_custom_health_check(self, name: str) -> str:
        """Run a custom health check"""
        if name not in self.health_checks:
            return f"❌ Health check '{name}' not found"

        check_info = self.health_checks[name]
        try:
            result = check_info["function"]()
            check_info["last_check"] = datetime.now()
            check_info["status"] = "passed" if result.get("healthy", True) else "failed"

            if not result.get("healthy", True):
                alert_msg = f"Custom health check failed: {name}"
                notification_skill.send_notification("telegram", alert_msg, "high")

            return f"✅ Health check '{name}': {result}"
        except Exception as e:
            check_info["status"] = "error"
            return f"❌ Health check '{name}' failed: {str(e)}"

    def get_watchdog_status(self) -> str:
        """Get status of the watchdog system"""
        monitored_count = len(self.monitored_processes)
        checks_count = len(self.health_checks)

        lines = [
            "🐕 **Self-Healing Watchdog Status**",
            f"• Monitored processes: {monitored_count}",
            f"• Custom health checks: {checks_count}",
            f"• Auto-restart: {'✅' if self.auto_restart_enabled else '❌'}",
            f"• Last health check: {self.last_health_check.strftime('%Y-%m-%d %H:%M:%S')}",
        ]

        if monitored_count > 0:
            lines.append("• **Processes**:")
            for name, info in self.monitored_processes.items():
                status = info["status"]
                pid = info["pid"] or "N/A"
                restarts = info["restart_count"]
                lines.append(f"  - {name}: {status} (PID: {pid}, restarts: {restarts})")

        return "\n".join(lines)

    def enable_auto_restart(self) -> str:
        """Enable automatic process restarting"""
        self.auto_restart_enabled = True
        return "✅ Auto-restart enabled"

    def disable_auto_restart(self) -> str:
        """Disable automatic process restarting"""
        self.auto_restart_enabled = False
        return "❌ Auto-restart disabled"


# Global instance
self_healing_skill = SelfHealingSkill()
