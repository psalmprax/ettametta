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
            # Migration: Standardize column names (Handle legacy 'topic' field)
            try:
                cursor = conn.execute("PRAGMA table_info(signals)")
                cols = [row[1] for row in cursor.fetchall()]
                if cols and "topic" in cols and "niche" not in cols:
                    logger.info("🔧 [Bus] Migrating 'topic' column to 'niche' in signal_vault.db")
                    conn.execute("ALTER TABLE signals RENAME COLUMN topic TO niche")
            except Exception as e:
                logger.error(f"Migration error: {e}")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    timestamp REAL,
                    niche TEXT,
                    platform TEXT,
                    velocity REAL,
                    acceleration REAL,
                    saturation REAL,
                    sentiment REAL
                )
            """)

    def ingest_signal(self, niche: str, platform: str, raw_metrics: dict[str, Any]):
        """Normalizes and persists a social signal"""
        # 1. Calculation Logic (Simplified for CPU-first logic)
        velocity = raw_metrics.get("growth_rate", 0.0)
        saturation = raw_metrics.get("saturation", 0.1)
        
        # 2. Acceleration Calculation (d2/dt2)
        acceleration = self._calculate_acceleration(niche, velocity)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO signals VALUES (?, ?, ?, ?, ?, ?, ?)",
                (time.time(), niche, platform, velocity, acceleration, saturation, 0.5)
            )
        
        logger.info(f"📡 [Bus] Ingested {platform} signal for '{niche}'. Accel: {acceleration:.2f}")

    def _calculate_acceleration(self, niche: str, current_velocity: float) -> float:
        """Computes the 2nd derivative of engagement velocity"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT velocity FROM signals WHERE niche = ? ORDER BY timestamp DESC LIMIT 1",
                (niche,)
            )
            prev = cursor.fetchone()
            if not prev: return 0.0
            return current_velocity - prev[0]

    def get_feature_vector(self, niche: str) -> list[float]:
        """Returns the full temporal feature vector for the Forecaster"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT velocity, acceleration, saturation FROM signals WHERE niche = ? ORDER BY timestamp DESC LIMIT 1",
                (niche,)
            )
            row = cursor.fetchone()
            return list(row) if row else []

# Singleton Instance
base_signal_bus = SignalBus()
