import re
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

def clean_json_response(text: str) -> str:
    """
    Ultramodern JSON extraction and repair.
    Uses json_repair to find and fix JSON objects within conversational noise.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        try:
            return json.dumps(text)
        except Exception:
            return ""
    
    # 1. Strip markdown code blocks
    text = re.sub(r'```(?:json)?\s*(.*?)\s*```', r'\1', text, flags=re.DOTALL)
    
    # 2. Try to find JSON using json_repair
    try:
        from json_repair import repair_json
        # repair_json can often find the JSON even if there's noise around it
        repaired = repair_json(text, ensure_ascii=False)
        if repaired and repaired != "null":
            # Verify it's actually JSON by trying to load it
            json.loads(repaired)
            return repaired
    except Exception:
        pass

    # 3. Fallback to regex-based extraction
    start_match = re.search(r'[\{\[]', text)
    if start_match:
        start_idx = start_match.start()
        end_bracket = '}' if start_match.group(0) == '{' else ']'
        last_idx = text.rfind(end_bracket)
        if last_idx != -1 and last_idx > start_idx:
            candidate = text[start_idx:last_idx + 1].strip()
            try:
                from json_repair import repair_json
                repaired = repair_json(candidate, ensure_ascii=False)
                if repaired and repaired != "null":
                    return repaired
            except Exception:
                return candidate
    
    return text.strip()

def repair_and_load_json(text: str) -> Any:
    """
    Attempts to clean, repair, and load JSON from an LLM response.
    """
    if not text:
        return None
        
    cleaned = clean_json_response(text)
    if not cleaned or cleaned == "null":
        return None
        
    try:
        return json.loads(cleaned)
    except Exception as e:
        # Last ditch effort
        try:
            from json_repair import repair_json
            repaired = repair_json(text)
            return json.loads(repaired)
        except Exception:
            logger.exception(f"Failed to load JSON even after all repair attempts: {e}")
            return None
