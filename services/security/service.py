import os
import json
import datetime
import redis
from api.config import settings

class SecuritySentinel:
    """
    Dedicated Security Sentinel service for real-time monitoring and threat detection.
    """
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL.replace("//localhost", "//redis") if "//localhost" in settings.REDIS_URL else settings.REDIS_URL)
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
            "details": details
        }
        self.redis_client.lpush(self.log_key, json.dumps(event))
        self.redis_client.ltrim(self.log_key, 0, 999) # Keep last 1000 events
        
        print(f"[Sentinel] [{severity.upper()}] {event_type}: {details}")

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
            "dev_secret_key_change_me_in_production"  # Legacy
        ]
        if not settings.SECRET_KEY or any(settings.SECRET_KEY == key for key in insecure_keys):
            findings.append("CRITICAL: Default or missing SECRET_KEY detected.")
            score -= 50

        # 2. Check File Permissions (if running locally)
        env_file = ".env"
        if os.path.exists(env_file):
            mode = oct(os.stat(env_file).st_mode & 0o777)
            if mode != '0o600' and mode != '0o400' and os.environ.get("ENV") == "production":
                findings.append(f"WARNING: Sensitive file {env_file} has permissive mode: {mode}")
                score -= 10

        # 3. Check for exposed ports (placeholder for network scan logic)
        # In a real environment, this might query an internal meta-endpoint or run a safe local scan.
        
        report = {
            "score": max(0, score),
            "findings": findings,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        
        self.redis_client.set(self.health_key, json.dumps(report))
        return report

    def get_security_status(self) -> dict:
        """
        Retrieves the latest health score and logs.
        """
        health_data = self.redis_client.get(self.health_key)
        health = json.loads(health_data) if health_data else {"score": 0, "findings": ["Pending audit..."]}
        
        logs_raw = self.redis_client.lrange(self.log_key, 0, 19) # Last 20 logs
        logs = [json.loads(l) for l in logs_raw]
        
        return {
            "health": health,
            "recent_events": logs,
            "threat_level": "LOW" if health["score"] > 80 else "CRITICAL" if health["score"] < 50 else "MEDIUM"
        }

base_security_sentinel = SecuritySentinel()
