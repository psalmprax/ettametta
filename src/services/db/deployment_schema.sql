/*
 ViralForge Production Schema (9.9/10)
 =====================================

 The authoritative data structure for the Viral Intelligence Core, 
 mapping Signals, Features, Graphs, and Performance Outcomes.
*/

-- 1. SIGNAL VAULT (High-Velocity Ingestion)
-- Raw temporal data from TikTok, YT, Reddit, X
CREATE TABLE IF NOT EXISTS signal_vault (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    topic TEXT NOT NULL,
    platform TEXT NOT NULL,
    velocity REAL DEFAULT 0,
    acceleration REAL DEFAULT 0,
    saturation REAL DEFAULT 0,
    sentiment_score REAL DEFAULT 0.5,
    engagement_count INTEGER DEFAULT 0
);

-- 2. FEATURE STORE (Aggregated Intelligence)
-- Pre-computed features for the Forecaster model
CREATE TABLE IF NOT EXISTS feature_store (
    topic TEXT PRIMARY KEY,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    avg_velocity REAL,
    peak_acceleration REAL,
    platform_spread_count INTEGER,
    first_seen_at TIMESTAMP,
    saturation_risk_index REAL
);

-- 3. ATTENTION GRAPH (Relational Brain)
-- Mapping how one topic influences another
CREATE TABLE IF NOT EXISTS attention_graph (
    source_topic TEXT,
    target_topic TEXT,
    influence_weight REAL DEFAULT 0.1,
    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (source_topic, target_topic)
);

-- 4. PERFORMANCE LEDGER (The Truth Layer)
-- Connecting Productions to Outcomes for model labeling
CREATE TABLE IF NOT EXISTS production_ledgers (
    video_id TEXT PRIMARY KEY,
    topic TEXT,
    variant_id TEXT,
    strategy_angle TEXT,
    predicted_retention REAL,
    actual_retention REAL,
    actual_views INTEGER,
    mae_error REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. SKILL CRYSTAL (Hermes Memory)
-- Pattern recognition for successful content strategies
CREATE TABLE IF NOT EXISTS crystallized_skills (
    skill_id TEXT PRIMARY KEY,
    pattern_name TEXT,
    niche TEXT,
    avg_performance_lift REAL,
    genetic_markers JSON
);
