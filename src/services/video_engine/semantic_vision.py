"""
Semantic Vision Service for Elite Cinematic Fusion
===================================================

Uses CLIP (Contrastive Language-Image Pre-training) to understand 
the visual content of video assets and find the best match for script lines.
"""

import os
import logging
import sqlite3
import json
from typing import List, Dict, Any, Optional
import numpy as np
import faiss
from PIL import Image

try:
    import torch
    from transformers import CLIPProcessor, CLIPModel
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    CLIPProcessor = None
    CLIPModel = None

logger = logging.getLogger(__name__)

class SemanticVision:
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
            self.faiss_index = faiss.IndexFlatIP(512) # CLIP VIT-B/32 uses 512 dimensions
            return

        embeddings = []
        for i, row in enumerate(rows):
            clip_id, emb_json = row
            emb = np.array(json.loads(emb_json)).astype('float32')
            embeddings.append(emb)
            self.id_to_metadata[i] = clip_id

        # Normalize and build index
        embeddings = np.array(embeddings)
        faiss.normalize_L2(embeddings)
        
        self.faiss_index = faiss.IndexFlatIP(512) # Inner product on normalized vectors = Cosine sim
        self.faiss_index.add(embeddings)
        logger.info(f"[Vision] FAISS Index loaded with {len(rows)} vectors.")

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

    def get_text_embedding(self, text: str) -> Optional[np.ndarray]:
        """Generates an embedding vector for a piece of text"""
        self._load_model()
        if not self.model or not self.processor: return None

        try:
            inputs = self.processor(text=[text], return_tensors="pt", padding=True)
            with torch.no_grad():
                text_features = self.model.get_text_features(**inputs)
            # Normalize and convert to numpy
            embedding = text_features.numpy()[0]
            return embedding / np.linalg.norm(embedding)
        except Exception as e:
            logger.error(f"[Vision] Text embedding failed: {e}")
            return None

    def analyze_scene(self, clip_path: str, thumbnail: Image.Image, timestamp: float = 0.0, motion_frame: Image.Image = None) -> Dict[str, Any]:
        """Analyzes a scene's semantics and motion energy"""
        self._load_model()
        if not self.model or not self.processor: return {}

        try:
            # 1. Semantic Embedding (CLIP)
            inputs = self.processor(images=thumbnail, return_tensors="pt")
            with torch.no_grad():
                image_features = self.model.get_image_features(**inputs)
            
            embedding = image_features.numpy()[0]
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

    def find_top_k_matches(self, query: str, k: int = 5, candidate_paths: List[str] = None) -> List[Dict[str, Any]]:
        """
        Finds the Top K matches in memory using FAISS.
        """
        query_embedding = self.get_text_embedding(query)
        if query_embedding is None or self.faiss_index is None: return []

        # FAISS search
        query_vector = np.array([query_embedding]).astype('float32')
        faiss.normalize_L2(query_vector)
        
        # Pull enough results to account for filtering if candidate_paths is provided
        search_k = k * 10 if candidate_paths else k
        scores, indices = self.faiss_index.search(query_vector, search_k)
        
        results = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for i, idx in enumerate(indices[0]):
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
                "score": float(scores[0][i]),
                "motion_score": motion
            })
            
            if len(results) >= k:
                break
            
        conn.close()
        return results

    def find_best_match(self, query: str, candidate_paths: List[str] = None) -> Optional[Dict[str, Any]]:
        """Finds the single best match using FAISS results"""
        results = self.find_top_k_matches(query, k=1, candidate_paths=candidate_paths)
        return results[0] if results else None

# Singleton instance
base_semantic_vision = SemanticVision()
