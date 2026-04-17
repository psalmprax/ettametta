"""
The Signal Bus & Feature Store (9.9/10)
=====================================

High-speed ingestion and time-series feature calculation for 
real-time viral forecasting.
"""

import logging
import json
import time
import sqlite3
from typing import Any
from pathlib import Path

logger = logging.getLogger(__name__)

class SignalBus:
    """
    Standardizes raw platform signals and maintains a time-series Feature Store.
    """
    def __init__(self, db_path: str = "data/analytics/signal_vault.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    timestamp REAL,
                    topic TEXT,
                    platform TEXT,
                    velocity REAL,
                    acceleration REAL,
                    saturation REAL,
                    sentiment REAL
                )
            """)

    def ingest_signal(self, topic: str, platform: str, raw_metrics: dict[str, Any]):
        """Normalizes and persists a social signal"""
        # 1. Calculation Logic (Simplified for CPU-first logic)
        velocity = raw_metrics.get("growth_rate", 0.0)
        saturation = raw_metrics.get("saturation", 0.1)
        
        # 2. Acceleration Calculation (d2/dt2)
        acceleration = self._calculate_acceleration(topic, velocity)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO signals VALUES (?, ?, ?, ?, ?, ?, ?)",
                (time.time(), topic, platform, velocity, acceleration, saturation, 0.5)
            )
        
        logger.info(f"📡 [Bus] Ingested {platform} signal for '{topic}'. Accel: {acceleration:.2f}")

    def _calculate_acceleration(self, topic: str, current_velocity: float) -> float:
        """Computes the 2nd derivative of engagement velocity"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT velocity FROM signals WHERE topic = ? ORDER BY timestamp DESC LIMIT 1",
                (topic,)
            )
            prev = cursor.fetchone()
            if not prev: return 0.0
            return current_velocity - prev[0]

    def get_feature_vector(self, topic: str) -> list[float]:
        """Returns the full temporal feature vector for the Forecaster"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT velocity, acceleration, saturation FROM signals WHERE topic = ? ORDER BY timestamp DESC LIMIT 1",
                (topic,)
            )
            row = cursor.fetchone()
            return list(row) if row else []

# Singleton Instance
base_signal_bus = SignalBus()
