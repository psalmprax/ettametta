import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional
from api.config import settings
from skills.memory import memory_skill

logger = logging.getLogger(__name__)


class NotificationSkill:
    def __init__(self):
        self.api_url = f"{settings.API_URL}"
        self.notification_log: List[Dict] = []
        self.webhooks: Dict[str, str] = {}
        self.alert_rules: List[Dict] = []

    def _get_headers(self):
        headers = {}
        if settings.INTERNAL_API_TOKEN:
            headers["Authorization"] = f"Bearer {settings.INTERNAL_API_TOKEN}"
        return headers

    def send_notification(
        self,
        channel: str,
        message: str,
        priority: str = "normal",
        metadata: Optional[Dict] = None,
    ) -> str:
        notification = {
            "channel": channel,
            "message": message,
            "priority": priority,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
            "status": "sent",
        }

        if channel == "telegram":
            return self._send_telegram(message, priority)
        elif channel == "webhook":
            return self._send_webhook(message, metadata)
        elif channel == "email":
            return self._send_email(message, metadata)
        elif channel == "dashboard":
            return self._send_dashboard(message, priority)
        elif channel == "all":
            results = []
            for ch in ["telegram", "webhook", "dashboard"]:
                if ch == "webhook" and not self.webhooks:
                    results.append(f"⚠️ {ch}: No webhooks configured")
                    continue
                resp = self.send_notification(ch, message, priority, metadata)
                results.append(f"{ch}: {resp[:50]}")
            return "📢 **Broadcast Results**:\n" + "\n".join(results)
        else:
            return f"⚠️ Unknown channel: {channel}. Supported: telegram, webhook, email, dashboard, all"

    def _send_telegram(self, message: str, priority: str = "normal") -> str:
        try:
            admin_id = settings.TELEGRAM_ADMIN_ID
            if not admin_id or not settings.TELEGRAM_BOT_TOKEN:
                return "⚠️ Telegram not configured"

            prefix = {"high": "🚨 ", "critical": "🔴 URGENT: ", "normal": ""}.get(
                priority, ""
            )
            url = (
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            )
            resp = requests.post(
                url,
                json={
                    "chat_id": admin_id,
                    "text": f"{prefix}{message}",
                    "parse_mode": "Markdown",
                },
                timeout=10,
            )

            if resp.status_code == 200:
                return f"✅ Telegram notification sent"
            else:
                return f"⚠️ Telegram failed: {resp.status_code}"
        except Exception as e:
            return f"⚠️ Telegram Error: {e}"

    def _send_webhook(self, message: str, metadata: Optional[Dict] = None) -> str:
        if not self.webhooks:
            return "⚠️ No webhooks configured. Use /notify webhook-add <url>"

        results = []
        for name, url in self.webhooks.items():
            try:
                payload = {
                    "message": message,
                    "metadata": metadata,
                    "timestamp": datetime.now().isoformat(),
                }
                resp = requests.post(url, json=payload, timeout=10)
                status = "✅" if resp.status_code < 300 else "⚠️"
                results.append(f"{status} {name}: {resp.status_code}")
            except Exception as e:
                results.append(f"❌ {name}: {e}")

        return "📡 **Webhook Results**:\n" + "\n".join(results)

    def _send_email(self, message: str, metadata: Optional[Dict] = None) -> str:
        return "⚠️ Email notifications not yet configured. Set up SMTP in .env"

    def _send_dashboard(self, message: str, priority: str = "normal") -> str:
        try:
            memory_skill.record_event(
                "dashboard_notification",
                {
                    "message": message,
                    "priority": priority,
                },
            )
            return "✅ Dashboard notification recorded"
        except Exception as e:
            return f"⚠️ Dashboard Error: {e}"

    def add_webhook(self, name: str, url: str) -> str:
        self.webhooks[name] = url
        return f"✅ Webhook '{name}' added: {url}"

    def remove_webhook(self, name: str) -> str:
        if name in self.webhooks:
            del self.webhooks[name]
            return f"✅ Webhook '{name}' removed"
        return f"⚠️ Webhook '{name}' not found"

    def list_webhooks(self) -> str:
        if not self.webhooks:
            return "📡 No webhooks configured."
        lines = ["📡 **Configured Webhooks**:", ""]
        for name, url in self.webhooks.items():
            lines.append(f"• {name}: {url}")
        return "\n".join(lines)

    def add_alert_rule(self, rule: Dict) -> str:
        self.alert_rules.append(rule)
        return f"✅ Alert rule added: {rule.get('name', 'unnamed')}"

    def check_alert_rules(self, data: Dict) -> List[str]:
        triggered = []
        for rule in self.alert_rules:
            condition = rule.get("condition", {})
            metric = condition.get("metric")
            threshold = condition.get("threshold")
            operator = condition.get("operator", ">")

            if metric and metric in data:
                value = data[metric]
                if isinstance(value, (int, float)) and isinstance(
                    threshold, (int, float)
                ):
                    if operator == ">" and value > threshold:
                        triggered.append(rule)
                    elif operator == "<" and value < threshold:
                        triggered.append(rule)
                    elif operator == ">=" and value >= threshold:
                        triggered.append(rule)
                    elif operator == "<=" and value <= threshold:
                        triggered.append(rule)

        for rule in triggered:
            channel = rule.get("channel", "telegram")
            message = rule.get(
                "message", f"Alert: {rule.get('name', 'unnamed')} triggered!"
            )
            self.send_notification(channel, message, rule.get("priority", "high"))

        return [r["name"] for r in triggered]

    def get_notification_log(self, limit: int = 20) -> str:
        notifications = memory_skill.episodic.search(
            event_type="dashboard_notification", limit=limit
        )
        if not notifications:
            return "📋 No notifications in log."

        lines = [f"📋 **Notification Log** ({len(notifications)}):"]
        for n in reversed(notifications):
            ts = n["timestamp"][:19]
            msg = n["data"].get("message", "")[:100]
            priority = n["data"].get("priority", "normal")
            icon = (
                "🔴" if priority == "critical" else "🟡" if priority == "high" else "🟢"
            )
            lines.append(f"{icon} [{ts}] {msg}")
        return "\n".join(lines)

    def setup_default_alerts(self) -> str:
        default_rules = [
            {
                "name": "viral_spike",
                "condition": {"metric": "views", "threshold": 10000, "operator": ">"},
                "channel": "telegram",
                "message": "🔥 Viral spike detected! A post just crossed 10K views.",
                "priority": "high",
            },
            {
                "name": "agent_zero_error",
                "condition": {
                    "metric": "error_count",
                    "threshold": 5,
                    "operator": ">=",
                },
                "channel": "telegram",
                "message": "⚠️ Agent Zero has encountered 5+ errors. Check status.",
                "priority": "high",
            },
            {
                "name": "storage_warning",
                "condition": {
                    "metric": "storage_used_pct",
                    "threshold": 80,
                    "operator": ">",
                },
                "channel": "telegram",
                "message": "💾 Storage warning: Over 80% used. Consider cleanup.",
                "priority": "normal",
            },
            {
                "name": "revenue_milestone",
                "condition": {
                    "metric": "daily_revenue",
                    "threshold": 100,
                    "operator": ">",
                },
                "channel": "telegram",
                "message": "💰 Revenue milestone: Daily revenue exceeded $100!",
                "priority": "normal",
            },
        ]

        for rule in default_rules:
            self.alert_rules.append(rule)

        return f"✅ {len(default_rules)} default alert rules configured:\n" + "\n".join(
            f"• {r['name']}: {r['condition']['metric']} {r['condition']['operator']} {r['condition']['threshold']}"
            for r in default_rules
        )


notification_skill = NotificationSkill()
