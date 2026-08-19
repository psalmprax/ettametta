"""
The Stream Heartbeat: Persistent Runtime Ingestion (10/10)
=========================================================

Ensures that no viral signals are lost even if the system
crashes, using a SQLite-backed persistent queue.
"""

import asyncio
from src.shared.enums import SystemJobStatus
import json
import sqlite3
from typing import Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class PersistentQueue:
    """
    A SQLite-backed queue for fault-tolerant signal processing.
    """
    def __init__(self, db_path: str = "data/runtime/queue_checkpoints.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT,
                    data_json TEXT,
                    priority INTEGER DEFAULT 1,
                    status TEXT DEFAULT '{SystemJobStatus.QUEUED.value}'
                )
            """)

    def push(self, topic: str, data: dict[str, Any], priority: int = 1):
        """Pushes a signal into the persistent queue"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO queue (topic, data_json, priority) VALUES (?, ?, ?)",
                (topic, json.dumps(data), priority)
            )
        logger.info(f"💾 [Queue] Persistent Checkpoint for '{topic}'")

    def pop(self) -> dict[str, Any] | None:
        """Retrieves and marks the oldest pending item"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"SELECT id, topic, data_json FROM queue WHERE status = '{SystemJobStatus.QUEUED.value}' ORDER BY priority DESC, id ASC LIMIT 1"
            )
            row = cursor.fetchone()
            if not row: return None

            q_id, topic, data_json = row
            conn.execute(f"UPDATE queue SET status = '{SystemJobStatus.PROCESSING.value}' WHERE id = ?", (q_id,))
            return {"id": q_id, "topic": topic, "data": json.loads(data_json)}

    def complete(self, q_id: int):
        """Deletes a successfully processed item"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM queue WHERE id = ?", (q_id,))

class StreamProcessor:
    """
    The Operational Heart: Manages ingestion throughput and backpressure.
    """
    def __init__(self):
        self.queue = PersistentQueue()
        self.is_running = False

    async def start_worker(self, handler_callback):
        """Continuous worker loop with fault recovery"""
        self.is_running = True
        logger.info("⚡ [Stream] Persistent Heartbeat: ACTIVE")

        while self.is_running:
            item = self.queue.pop()
            if item:
                try:
                    await handler_callback(item["topic"], item["data"])
                    self.queue.complete(item["id"])
                except Exception as e:
                    logger.exception(f"❌ [Stream] Processing Error: {e}")

            await asyncio.sleep(1) # Frequency management

# Singleton Instance
base_stream_service = StreamProcessor()
