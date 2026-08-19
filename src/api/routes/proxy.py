from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
import os
import json
import logging
from src.api.config import settings
from src.api.utils.json_cleaner import clean_json_response, repair_and_load_json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/proxy", tags=["Proxy"])

@router.get("/status")
async def proxy_status():
    return {"status": "active", "proxy_targets": ["ollama"]}

@router.post("/ollama/{path:path}")
async def proxy_ollama(path: str, request: Request):
    try:
        body = await request.json()

        if not isinstance(body, dict):
            logger.warning(f"⚠️ [OllamaProxy] Body is {type(body)}, not dict. Raw: {body}")
            # Try to force it to dict if it's a string
            if isinstance(body, str):
                try:
                    body = json.loads(body)
                except Exception:
                    body = {"payload": body}
            else:
                body = {"payload": body}
    except Exception as e:
        logger.exception(f"❌ [OllamaProxy] JSON parse failed: {e}")
        body = {}

    ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434").rstrip("/")

    # Clean the path: Remove leading 'v1/' if present
    clean_path = path.lstrip("/")
    if clean_path.startswith("v1/"):
        clean_path = clean_path[3:].lstrip("/")

    # Protocol Mapping
    translate_to_openai = False
    target_path = clean_path

    # Model Mapping (Bypass library whitelists)
    if "model" in body:
        original_model = body["model"]
        if any(x in original_model.lower() for x in ["gpt-", "claude-", "ollama/", "o4-", "gemini-"]):
            body["model"] = settings.OLLAMA_MODEL
            logger.info(f"🎯 [OllamaProxy] Remapping model: {original_model} -> {body['model']}")

    # Parameter Sanitization (Handle gpt-researcher/langchain None values)
    if "temperature" in body:
        if body["temperature"] is None:
            body["temperature"] = 0.7
        else:
            try:
                body["temperature"] = float(body["temperature"])
            except (ValueError, TypeError):
                body["temperature"] = 0.7

    if "max_tokens" in body and body["max_tokens"] is None:
        body["max_tokens"] = 4096

    # Remove unsupported parameters that might cause 400s in Ollama/vLLM
    unsupported = ["top_n", "stream_options", "user_id"]
    for param in unsupported:
        body.pop(param, None)

    # Force non-streaming if not explicitly requested
    if not body.get("stream"):
        body["stream"] = False

    # OpenAI Chat -> Ollama Native
    if target_path == "chat/completions":
        target_path = "api/chat"
        translate_to_openai = True

    # OpenAI Embeddings -> Ollama Native
    if target_path == "embeddings":
        target_path = "api/embeddings"
        translate_to_openai = True
        # Ollama expects 'prompt' instead of 'input'
        inputs = body.get("input", "")
        if isinstance(inputs, list):
            # Batch loop for sequential embeddings (Ollama native often lacks batch)
            embeddings_results = []
            async with httpx.AsyncClient(timeout=600.0) as client:
                for idx, text in enumerate(inputs):
                    logger.info(f"🧬 [OllamaProxy] Sequential Embedding {idx+1}/{len(inputs)}")
                    resp = await client.post(f"{ollama_url}/api/embeddings", json={"model": body["model"], "prompt": text})
                    if resp.status_code == 200:
                        embeddings_results.append(resp.json().get("embedding", []))
                    else:
                        err_text = resp.text
                        logger.error(f"❌ [OllamaProxy] Sequential Embedding failed: {resp.status_code}. Raw: {err_text}")
                        embeddings_results.append([])

            return {
                "object": "list",
                "data": [{"object": "embedding", "index": i, "embedding": emb} for i, emb in enumerate(embeddings_results)],
                "model": body.get("model", ""),
                "usage": {"prompt_tokens": 0, "total_tokens": 0}
            }
        else:
            body["prompt"] = inputs

    # OpenAI Models -> Ollama Tags
    if target_path == "models":
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{ollama_url}/api/tags")
            if resp.status_code == 200:
                tags = resp.json().get("models", [])
                return {
                    "object": "list",
                    "data": [
                        {
                            "id": t.get("name"),
                            "object": "model",
                            "created": 0,
                            "owned_by": "ollama"
                        } for t in tags
                    ]
                }
            return resp.json()

    target_url = f"{ollama_url}/{target_path}"

    # Debug log the translation
    logger.info(f"🔄 [OllamaProxy] Path: {path} -> Target: {target_url}")

    if body.get("stream", False):
        return await proxy_streaming(target_url, body, translate_to_openai)

    async with httpx.AsyncClient(timeout=600.0) as client:
        try:
            resp = await client.post(target_url, json=body)
            raw_text = resp.text

            try:
                data = resp.json()
            except json.JSONDecodeError:
                data = repair_and_load_json(raw_text)
                if not data:
                    logger.exception(f"❌ [OllamaProxy] Parse failure on {target_url}. Raw: {raw_text[:200]}")
                    raise HTTPException(status_code=502, detail="Upstream protocol error")

            if resp.status_code != 200:
                logger.warning(f"⚠️ [OllamaProxy] Upstream {resp.status_code} for {target_url}. Raw: {raw_text[:100]}")
                return JSONResponse(status_code=resp.status_code, content=data)

            # Native Ollama -> OpenAI Conversion
            if translate_to_openai and isinstance(data, dict):
                if "api/chat" in target_path:
                    # If it's already OpenAI format (Ollama sometimes does this now)
                    if "choices" in data:
                        return data

                    content = data.get("message", {}).get("content", "")
                    sanitized = clean_json_response(content)
                    data = {
                        "id": "chatcmpl-local", "object": "chat.completion", "created": 0,
                        "model": body.get("model", ""),
                        "choices": [{"index": 0, "message": {"role": "assistant", "content": sanitized}, "finish_reason": "stop"}]
                    }
                elif "api/embeddings" in target_path and isinstance(data, dict):
                    # Handle batch embeddings if input was a list
                    inputs = body.get("prompt", body.get("input", ""))
                    if isinstance(inputs, str):
                        inputs = [inputs]

                    embeddings_data = []
                    # If the response already has multiple embeddings (batch support in upstream)
                    if "embeddings" in data:
                        for i, emb in enumerate(data["embeddings"]):
                            embeddings_data.append({"object": "embedding", "index": i, "embedding": emb})
                    else:
                        # Fallback for single embedding response
                        embedding = data.get("embedding", [])
                        embeddings_data.append({"object": "embedding", "index": 0, "embedding": embedding})

                    data = {
                        "object": "list",
                        "data": embeddings_data,
                        "model": body.get("model", ""),
                        "usage": {"prompt_tokens": 0, "total_tokens": 0}
                    }

            return data

        except Exception as e:
            logger.exception(f"❌ [OllamaProxy] Proxy critical failure: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

async def proxy_streaming(url: str, body: dict, translate: bool):
    async def generate():
        async with httpx.AsyncClient(timeout=600.0) as client:
            async with client.stream("POST", url, json=body) as resp:
                async for chunk in resp.aiter_lines():
                    if not chunk:
                        continue
                    if translate:
                        try:
                            ollama_data = json.loads(chunk)
                            content = ollama_data.get("message", {}).get("content", "")
                            done = ollama_data.get("done", False)
                            openai_chunk = {
                                "id": "chatcmpl-local", "object": "chat.completion.chunk", "created": 0,
                                "model": body.get("model", ""),
                                "choices": [{"index": 0, "delta": {"content": content}, "finish_reason": "stop" if done else None}]
                            }
                            yield f"data: {json.dumps(openai_chunk)}\n\n".encode('utf-8')
                            if done:
                                yield b"data: [DONE]\n\n"
                        except Exception:
                            yield f"data: {chunk}\n\n".encode('utf-8')
                    else:
                        yield (chunk + "\n").encode('utf-8')
    return StreamingResponse(generate(), media_type="text/event-stream" if translate else "application/x-ndjson")
