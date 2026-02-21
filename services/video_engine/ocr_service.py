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
        """
        detections = self.detect_text_regions(video_path)
        if not detections:
            return "bottom"

        # Count how many detections are in the bottom half
        bottom_half_count = sum(1 for d in detections if d["normalized_y"] > 0.6)
        top_half_count = sum(1 for d in detections if d["normalized_y"] < 0.4)
        
        logging.info(f"[OCRService] Detected {len(detections)} text regions. Bottom: {bottom_half_count}, Top: {top_half_count}")

        if bottom_half_count > top_half_count:
            # Source already has captions/text at the bottom
            return "top"
        elif top_half_count > 0 and bottom_half_count == 0:
            return "bottom"
        elif bottom_half_count > 0 and top_half_count > 0:
            # Text everywhere, maybe center or top with high visibility
            return "top"
            
        return "bottom"

ocr_service = OCRService()
