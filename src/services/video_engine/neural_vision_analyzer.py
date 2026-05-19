"""
Neural Vision Service for Elite Cinematic Fusion
===================================================

Uses CLIP (Contrastive Language-Image Pre-training) to understand 
the visual content of video assets and find the best match for script lines.
"""

import os
import logging
import sqlite3
import json
from typing import Any
import numpy as np
from PIL import Image

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

try:
    import torch
    from transformers import CLIPProcessor, CLIPModel
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    CLIPProcessor = None
    CLIPModel = None

logger = logging.getLogger(__name__)

class NeuralVisionAnalyzer:
    """
    Handles visual understanding and semantic matching.
    """

    def __init__(self, db_path: str = "data/db/visual_memory.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
        
        self.model = None
        self.processor = None
        self.device = "cpu"
        
        self.faiss_index = None
        self.id_to_metadata = {} # Map FAISS index to SQLite IDs
        self._load_faiss_index()

    def _init_db(self):
        """Initialize the Visual Memory database"""
        conn = sqlite3.connect(self.db_path)
        # 10/10 Production: Resilient Schema Enforcement
        conn.execute("""
            CREATE TABLE IF NOT EXISTS visual_index (
                id TEXT PRIMARY KEY,
                clip_path TEXT,
                timestamp REAL,
                embedding_json TEXT,
                description TEXT,
                motion_score REAL
            )
        """)
        # Ensure motion_score column exists for legacy databases
        try:
            conn.execute("ALTER TABLE visual_index ADD COLUMN motion_score REAL")
        except sqlite3.OperationalError:
            pass # Column already exists
            
        conn.commit()
        conn.close()

    def _load_faiss_index(self):
        """Build or load a FAISS index from the SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, embedding_json FROM visual_index")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            # Create empty index
            if FAISS_AVAILABLE:
                self.faiss_index = faiss.IndexFlatIP(512) # CLIP VIT-B/32 uses 512 dimensions
            else:
                self.faiss_index = np.empty((0, 512), dtype='float32')
            return

        embeddings = []
        for i, row in enumerate(rows):
            clip_id, emb_json = row
            embeddings.append(json.loads(emb_json))
            self.id_to_metadata[i] = clip_id

        # Normalize and build index
        embeddings = np.array(embeddings, dtype='float32')
        if FAISS_AVAILABLE:
            faiss.normalize_L2(embeddings)
            self.faiss_index = faiss.IndexFlatIP(512) # Inner product on normalized vectors = Cosine sim
            self.faiss_index.add(embeddings)
        else:
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self.faiss_index = embeddings / norms
        logger.info(f"[Vision] FAISS Index loaded with {len(rows)} vectors (FAISS available: {FAISS_AVAILABLE}).")

    def _load_model(self):
        """Lazy load the CLIP model to save memory"""
        if self.model is None and TORCH_AVAILABLE:
            try:
                logger.info("[Vision] Loading CLIP model (openai/clip-vit-base-patch32) on CPU...")
                self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
                self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
                logger.info("[Vision] CLIP Model loaded successfully.")
            except Exception as e:
                logger.error(f"[Vision] Failed to load CLIP model: {e}")

    def get_text_embedding(self, text: str) -> np.ndarray | None:
        """Generates an embedding vector for a piece of text"""
        self._load_model()
        if not self.model or not self.processor: return None

        try:
            inputs = self.processor(text=[text], return_tensors="pt", padding=True)
            with torch.no_grad():
                text_features = self.model.get_text_features(**inputs)
            # Normalize and convert to numpy — handle both tensor and model output types
            if hasattr(text_features, 'detach'):
                embedding = text_features.detach().cpu().numpy()[0]
            elif hasattr(text_features, 'pooler_output'):
                embedding = text_features.pooler_output.detach().cpu().numpy()[0]
            else:
                embedding = np.array(text_features[0]).flatten()[:512].astype('float32')
            return embedding / np.linalg.norm(embedding)
        except Exception as e:
            logger.error(f"[Vision] Text embedding failed: {e}")
            return None

    def analyze_scene(self, clip_path: str, thumbnail: Image.Image, timestamp: float = 0.0, motion_frame: Image.Image = None) -> dict[str, Any]:
        """Analyzes a scene's semantics and motion energy"""
        self._load_model()
        if not self.model or not self.processor: return {}

        try:
            # 1. Semantic Embedding (CLIP)
            inputs = self.processor(images=thumbnail, return_tensors="pt")
            with torch.no_grad():
                image_features = self.model.get_image_features(**inputs)
            
            # Handle both tensor and model output types
            if hasattr(image_features, 'detach'):
                embedding = image_features.detach().cpu().numpy()[0]
            elif hasattr(image_features, 'pooler_output'):
                embedding = image_features.pooler_output.detach().cpu().numpy()[0]
            else:
                embedding = np.array(image_features[0]).flatten()[:512].astype('float32')
            embedding = embedding / np.linalg.norm(embedding)
            
            # 2. Motion Density (Ascension Tier)
            motion_score = 0.0
            if motion_frame:
                import cv2
                f1 = cv2.cvtColor(np.array(thumbnail), cv2.COLOR_RGB2GRAY)
                f2 = cv2.cvtColor(np.array(motion_frame), cv2.COLOR_RGB2GRAY)
                diff = cv2.absdiff(f1, f2)
                motion_score = float(np.mean(diff))

            # Store in DB
            clip_id = f"{os.path.basename(clip_path)}_{timestamp:.2f}"
            embedding_json = json.dumps(embedding.tolist())
            
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "INSERT OR REPLACE INTO visual_index (id, clip_path, timestamp, embedding_json, motion_score) VALUES (?,?,?,?,?)",
                (clip_id, clip_path, timestamp, embedding_json, motion_score)
            )
            conn.commit()
            conn.close()
            
            # Rebuild FAISS index to include new vector
            self._load_faiss_index()
            
            return {"id": clip_id, "embedding": embedding, "motion_score": motion_score}
        except Exception as e:
            logger.error(f"[Vision] Scene analysis failed: {e}")
            return {}

    def find_top_k_matches(self, query: str, k: int = 5, candidate_paths: list[str] = None) -> list[dict[str, Any]]:
        """
        Finds the Top K matches in memory using FAISS or NumPy.
        """
        query_embedding = self.get_text_embedding(query)
        if query_embedding is None or self.faiss_index is None: return []

        # FAISS or NumPy search
        query_vector = np.array([query_embedding]).astype('float32')
        
        # Pull enough results to account for filtering if candidate_paths is provided
        search_k = k * 10 if candidate_paths else k
        
        if FAISS_AVAILABLE:
            faiss.normalize_L2(query_vector)
            scores, indices = self.faiss_index.search(query_vector, search_k)
            scores = scores[0]
            indices = indices[0]
        else:
            # Cosine similarity using NumPy
            q_norm = np.linalg.norm(query_vector)
            if q_norm > 0:
                query_vector = query_vector / q_norm
                
            if len(self.faiss_index) == 0:
                scores, indices = [], []
            else:
                sims = np.dot(self.faiss_index, query_vector[0])
                indices = np.argsort(sims)[::-1]
                scores = sims[indices]
                
                scores = scores[:search_k]
                indices = indices[:search_k]
        
        results = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for i, idx in enumerate(indices):
            if idx == -1: continue # No further results
            
            clip_id = self.id_to_metadata.get(idx)
            if not clip_id: continue
            
            cursor.execute("SELECT clip_path, timestamp, motion_score FROM visual_index WHERE id = ?", (clip_id,))
            metadata = cursor.fetchone()
            if not metadata: continue
            
            path, ts, motion = metadata
            
            # Apply candidate filter if provided
            if candidate_paths and path not in candidate_paths:
                continue
                
            results.append({
                "path": path,
                "timestamp": ts,
                "score": float(scores[i]),
                "motion_score": motion
            })
            
            if len(results) >= k:
                break
            
        conn.close()
        return results

    def find_best_match(self, query: str, candidate_paths: list[str] = None) -> dict[str, Any] | None:
        """Finds the single best match using FAISS results"""
        results = self.find_top_k_matches(query, k=1, candidate_paths=candidate_paths)
        return results[0] if results else None

# Singleton instance
base_vision_service = NeuralVisionAnalyzer()
