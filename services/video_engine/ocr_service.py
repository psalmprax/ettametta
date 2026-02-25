import easyocr
import cv2
import os
import logging
import numpy as np
from typing import List, Dict, Tuple

class OCRService:
    def __init__(self):
        # Initialize reader once. This will download models on first run if not present.
        # We use English by default, but can be expanded.
        try:
            self.reader = easyocr.Reader(['en'], gpu=False) # GPU=False for OCI ARM compatibility
            logging.info("[OCRService] EasyOCR initialized.")
        except Exception as e:
            logging.error(f"[OCRService] Failed to initialize EasyOCR: {e}")
            self.reader = None

    def detect_text_regions(self, video_path: str, sample_rate: int = 30) -> List[Dict]:
        """
        Samples frames from a video and detects bounding boxes of text.
        Returns a list of regions found.
        """
        if not self.reader:
            return []

        cap = cv2.VideoCapture(video_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        all_detections = []
        
        # Sample frames (every 1 second or sample_rate frames)
        for i in range(0, frame_count, sample_rate):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if not ret:
                break
            
            # Perform OCR on the frame
            # EasyOCR returns: [ ([[x,y],[x,y],[x,y],[x,y]], text, confidence), ... ]
            results = self.reader.readtext(frame)
            
            for (bbox, text, prob) in results:
                if prob > 0.3: # Filter low confidence
                    # bbox is 4 points: tl, tr, br, bl
                    tl, tr, br, bl = bbox
                    all_detections.append({
                        "frame": i,
                        "text": text,
                        "confidence": prob,
                        "bbox": {
                            "xmin": int(min(tl[0], bl[0])),
                            "ymin": int(min(tl[1], tr[1])),
                            "xmax": int(max(tr[0], br[0])),
                            "ymax": int(max(bl[1], br[1]))
                        },
                        "normalized_y": (tl[1] + br[1]) / (2 * height) # 0 to 1
                    })
        
        cap.release()
        return all_detections

    def get_caption_strategy(self, video_path: str) -> str:
        """
        Analyzes the video and returns a placement strategy: 'bottom' (default), 'top', or 'center'.
        Uses a density-based 'Least Obstructive Path' approach.
        """
        detections = self.detect_text_regions(video_path)
        if not detections:
            return "bottom"

        # Divide into 5 vertical zones for higher precision
        # Zone 0: Top (0.0-0.2)
        # Zone 1: Upper Middle (0.2-0.4)
        # Zone 2: Middle (0.4-0.6)
        # Zone 3: Lower Middle (0.6-0.8)
        # Zone 4: Bottom (0.8-1.0)
        
        zones = [0, 0, 0, 0, 0]
        for d in detections:
            y = d["normalized_y"]
            idx = int(y * 5)
            if idx > 4: idx = 4
            zones[idx] += 1
            
        logging.info(f"[OCRService] Vertical Density Map: {zones}")

        # Priority 1: Use Bottom (Preferred for mobile)
        if zones[4] == 0 and zones[3] == 0:
            return "bottom"
        
        # Priority 2: Use Top (Secondary for mobile)
        if zones[0] == 0 and zones[1] == 0:
            return "top"
            
        # Priority 3: Use Center (Least desirable but fallback)
        if zones[2] == 0:
            return "center"
            
        # Priority 4: If everything is crowded, pick the zone with minimum density
        # We exclude center (index 2) from this pick if possible
        candidates = [0, 4] # Top vs Bottom
        best_zone = min(candidates, key=lambda i: zones[i])
        
        return "top" if best_zone == 0 else "bottom"

ocr_service = OCRService()
