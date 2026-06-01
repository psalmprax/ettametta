import os
import json
import datetime
import logging
import socket
import asyncio
from src.api.utils.redis import get_sync_redis

logger = logging.getLogger(__name__)


class SecuritySentinel:
    """
    Dedicated Security Sentinel service for real-time monitoring and threat detection.
    """

    def __init__(self):
        self.redis_client = get_sync_redis()
        self.log_key = "sentinel:security_logs"
        self.health_key = "sentinel:security_health"

    def log_event(self, event_type: str, severity: str, details: dict):
        """
        Logs a security event to Redis for real-time monitoring.
        """
        event = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "type": event_type,
            "severity": severity,
            "details": details,
        }
        self.redis_client.lpush(self.log_key, json.dumps(event))
        self.redis_client.ltrim(self.log_key, 0, 999)  # Keep last 1000 events

        logger.info(f"[Sentinel] [{severity.upper()}] {event_type}: {details}")

    def audit_system_integrity(self) -> dict:
        """
        Performs a system-wide integrity audit.
        """
        findings = []
        score = 100

        # 1. Check SECRET_KEY
        insecure_keys = [
            "dev_secret_key_change_me_in_production",
            "dev_secret_key_vforge_2026_change_in_prod",
            "dev_secret_key_change_me_in_production",  # Legacy
        ]
        if not settings.SECRET_KEY or any(
            settings.SECRET_KEY == key for key in insecure_keys
        ):
            findings.append("CRITICAL: Default or missing SECRET_KEY detected.")
            score -= 50

        # 2. Check File Permissions (if running locally)
        env_file = ".env"
        if os.path.exists(env_file):
            mode = oct(os.stat(env_file).st_mode & 0o777)
            if (
                mode != "0o600"
                and mode != "0o400"
                and os.environ.get("ENV") == "production"
            ):
                findings.append(
                    f"WARNING: Sensitive file {env_file} has permissive mode: {mode}"
                )
                score -= 10

        # 3. Check for exposed ports using socket connections
        dangerous_ports = [
            22,
            23,
            3306,
            5432,
            6379,
            27017,
        ]  # SSH, Telnet, DBs, Redis, Mongo

        for port in dangerous_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex(("127.0.0.1", port))
                sock.close()
                if result == 0:
                    findings.append(
                        f"WARNING: Port {port} is open on localhost (potential exposure)"
                    )
                    score -= 5
            except socket.error as e:
                logger.debug(f"Port scan failed for {port}: {e}")
            except Exception as e:
                logger.exception(f"Unexpected error during port scan: {e}")

        report = {
            "score": max(0, score),
            "findings": findings,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        # Store audit results
        self.redis_client.setex(
            f"{self.health_key}:audit:{datetime.datetime.now().date().isoformat()}",
            86400 * 7,  # 7 days
            json.dumps(report),
        )

        return report

    def get_security_status(self) -> dict:
        """
        Returns comprehensive security status with health score and recent events.
        """
        # Calculate dynamic health score
        score = self._calculate_health_score()

        # Get recent events
        events = []
        raw_events = self.redis_client.lrange(self.log_key, 0, 49)  # Last 50 events
        for event_json in raw_events:
            try:
                events.append(json.loads(event_json))
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                logger.warning(f"Failed to decode security event: {e}")

        # Categorize threat levels
        threat_levels = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for event in events[-100:]:  # Last 100 events for threat assessment
            severity = event.get("severity", "low").lower()
            threat_levels[severity] = threat_levels.get(severity, 0) + 1

        # Determine overall threat level
        if threat_levels["critical"] > 0:
            threat_level = "CRITICAL"
        elif threat_levels["high"] > 2:
            threat_level = "HIGH"
        elif threat_levels["medium"] > 5:
            threat_level = "MEDIUM"
        elif threat_levels["low"] > 10:
            threat_level = "LOW"
        else:
            threat_level = "NOMINAL"

        # Get system integrity status
        integrity = self._check_system_integrity()

        return {
            "health_score": score,
            "threat_level": threat_level,
            "recent_threats": events[:10],  # Last 10 events
            "system_integrity": integrity,
            "threat_breakdown": threat_levels,
            "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

    def _calculate_health_score(self) -> int:
        """Calculate dynamic security health score."""
        base_score = 100
        penalties = 0

        # Check for recent critical events
        critical_events = 0
        raw_events = self.redis_client.lrange(self.log_key, 0, 99)  # Last 100 events
        for event_json in raw_events:
            try:
                event = json.loads(event_json)
                if event.get("severity") == "critical":
                    critical_events += 1
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                logger.warning(f"Failed to decode security event for health score: {e}")

        penalties += critical_events * 20  # 20 points per critical event

        # Check API key health
        try:
            from src.api.config import settings

            if not settings.GROQ_API_KEY:
                penalties += 15
            if not settings.STRIPE_SECRET_KEY:
                penalties += 10
            if not settings.AWS_ACCESS_KEY_ID:
                penalties += 10
        except Exception as e:
            logger.warning(f"Failed to check API key health: {e}")
            penalties += 20  # Config issues

        # Check Redis connectivity
        try:
            self.redis_client.ping()
        except Exception as e:
            logger.exception(f"Redis connectivity failed: {e}")
            penalties += 30  # Redis down is critical

        return max(0, base_score - penalties)

    def _check_system_integrity(self) -> str:
        """Check overall system integrity."""
        issues = []

        # Check Redis
        try:
            self.redis_client.ping()
        except Exception as e:
            logger.exception(f"Redis health check failed: {e}")
            issues.append("Redis connectivity failed")

        # Check database
        try:
            from src.api.utils.database import async_session_factory
            from sqlalchemy import select

            async def check_db():
                async with async_session_factory() as db:
                    await db.execute(select(1))

            asyncio.run(check_db())
        except Exception as e:
            logger.exception(f"Database health check failed: {e}")
            issues.append("Database connectivity failed")

        # Check file system
        try:
            with open("/tmp/sentinel_health_check", "w") as f:
                f.write("ok")
            os.remove("/tmp/sentinel_health_check")
        except Exception as e:
            logger.exception(f"File system health check failed: {e}")
            issues.append("File system write permissions issue")

        if not issues:
            return "NOMINAL"
        elif len(issues) == 1:
            return "DEGRADED"
        else:
            return "CRITICAL"

    def monitor_api_requests(self, request, response, user_id=None):
        """Monitor API requests for security anomalies."""
        # Rate limiting check
        if hasattr(request, "client") and request.client:
            client_ip = request.client.host
            datetime.datetime.now().timestamp()

            # Track requests per IP
            ip_key = f"security:requests:{client_ip}"
            request_count = self.redis_client.incr(ip_key)
            self.redis_client.expire(ip_key, 300)  # 5 minute window

            if request_count > 100:  # More than 100 requests per 5 minutes
                self.log_event(
                    "RATE_LIMIT_EXCEEDED",
                    "high",
                    {"ip": client_ip, "requests": request_count, "window": "5min"},
                )

        # Suspicious patterns
        if response.status_code >= 400:
            self.log_event(
                "FAILED_REQUEST",
                "low",
                {
                    "endpoint": getattr(request, "url", {}).path
                    if hasattr(request, "url")
                    else str(request.url),
                    "status_code": response.status_code,
                    "user_id": user_id,
                },
            )

    def scan_for_vulnerabilities(self) -> dict:
        """Perform comprehensive vulnerability scan."""
        vulnerabilities = []

        # Check for common vulnerabilities
        try:
            import subprocess

            # Check for exposed debug endpoints
            result = subprocess.run(
                ["grep", "-r", "DEBUG.*=.*True", "/app"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                vulnerabilities.append(
                    {
                        "type": "DEBUG_MODE",
                        "severity": "high",
                        "description": "Debug mode enabled in production",
                        "details": result.stdout[:200] + "..."
                        if len(result.stdout) > 200
                        else result.stdout,
                    }
                )

            # Check for hardcoded secrets
            result = subprocess.run(
                ["grep", "-r", "password.*=", "/app", "--exclude-dir=.git"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.split("\n")
                vulnerabilities.append(
                    {
                        "type": "HARDCODED_SECRETS",
                        "severity": "critical",
                        "description": "Potential hardcoded secrets detected",
                        "details": f"Found {len(lines)} potential secret patterns",
                    }
                )

        except Exception as e:
            vulnerabilities.append(
                {
                    "type": "SCAN_ERROR",
                    "severity": "medium",
                    "description": f"Vulnerability scan failed: {str(e)}",
                }
            )

        {
            "scan_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "vulnerabilities_found": len(vulnerabilities),
            "vulnerabilities": vulnerabilities,
            "overall_risk": "CRITICAL"
            if any(v["severity"] == "critical" for v in vulnerabilities)
            else "HIGH"
            if any(v["severity"] == "high" for v in vulnerabilities)
            else "MEDIUM"
            if any(v["severity"] == "medium" for v in vulnerabilities)
            else "LOW",
        }

        try:
            self.redis_client.set(self.health_key, json.dumps(vulnerabilities))
        except Exception as e:
            logger.warning(f"Failed to cache security report: {e}")

        return vulnerabilities


base_security_service = SecuritySentinel()
