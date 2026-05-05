import os
import asyncio
import json
import logging
import time
import httpx
from typing import Any
from uuid import uuid4
from src.api.config import settings
from src.api.utils.tracing import get_request_id, setup_tracing_logger

# Configure Structured Logging (Standard 2.22)
logger = setup_tracing_logger("IntelligenceHub")


class CircuitBreaker:
    """
    Standard 1.14: Circuit Breaker with Exponential Backoff
    """

    def __init__(self, name: str, failure_threshold=3, recovery_timeout=30):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        logger.warning(
            json.dumps(
                {
                    "event": "circuit_breaker_failure",
                    "name": self.name,
                    "failure_count": self.failure_count,
                    "threshold": self.failure_threshold,
                    "state": self.state,
                }
            )
        )
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(
                json.dumps(
                    {
                        "event": "circuit_breaker_open",
                        "name": self.name,
                        "msg": f"Circuit breaker {self.name} is now OPEN",
                    }
                )
            )

    def record_success(self):
        if self.state != "CLOSED":
            logger.info(
                json.dumps(
                    {
                        "event": "circuit_breaker_closed",
                        "name": self.name,
                        "msg": f"Circuit breaker {self.name} is now CLOSED",
                    }
                )
            )
        self.failure_count = 0
        self.state = "CLOSED"

    def reset(self):
        """Manually reset the circuit breaker to CLOSED state."""
        if self.state != "CLOSED":
            logger.info(
                json.dumps(
                    {
                        "event": "circuit_breaker_manual_reset",
                        "name": self.name,
                        "msg": f"Circuit breaker {self.name} manually reset",
                    }
                )
            )
        self.failure_count = 0
        self.state = "CLOSED"

    def can_attempt(self) -> bool:
        """Check if circuit breaker allows requests."""
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False  # OPEN and still recovering
        if self.state == "HALF_OPEN":
            return True  # Allow test request
        return False  # Unknown state


class IntelligenceHub:
    """
    Unified Intelligence Model (Tier 10.0)
    Centralizes all LLM traffic with failover and hardening.
    """

    def __init__(self):
        self.openai_key = settings.OPENAI_API_KEY
        self.groq_key = settings.GROQ_API_KEY
        self.google_key = settings.GOOGLE_API_KEY
        # Corrected: Use settings and ensure endpoint suffix
        self.primary_ollama_url = settings.OLLAMA_URL.rstrip("/") + "/api/chat"
        self.fallback_ollama_url = "http://localhost:11434/api/chat"
        self.ollama_url = self.primary_ollama_url

        # Hardening: Dedicated Circuit Breakers per provider
        self.breakers = {
            "ollama": CircuitBreaker("Ollama-Local-Edge"),
            "openai": CircuitBreaker("OpenAI-Champion"),
            "groq": CircuitBreaker("Groq-Challenger"),
            "gemini": CircuitBreaker("Gemini-Titan"),
            "vllm": CircuitBreaker("vLLM-Production-Edge"),
        }

        # Primary/Champion configuration
        self.primary_provider = settings.DEFAULT_LLM_PROVIDER
        self.fallback_provider = settings.FALLBACK_LLM_PROVIDER

    async def chat(
        self,
        prompt: str,
        system_prompt: str = "You are a Viral Narrative Analyst.",
        session_id: str | None = None,
        json_mode: bool = False,
        complexity: str = "medium",  # "low", "medium", "high"
        provider: str | None = None, # Explicit provider override
        rag_context: str | None = None, # RAG context to inject
    ) -> dict[str, Any]:
        """
        Unified chat interface with complexity-based routing and failure persistence.
        """
        request_id = session_id or get_request_id()

        # Step 1: Route based on complexity
        primary = self._route_complexity(complexity)
        
        # Step 2: Define candidates (Primary -> Fallbacks)
        if provider:
            candidates = [provider]
        else:
            candidates = [primary, "vllm", "ollama", "gemini", "groq", "openai"]
        
        # Remove duplicates while preserving order
        candidates = list(dict.fromkeys(candidates))

        for p in candidates:
            if p not in self.breakers:
                logger.warning(f"Provider {p} not in breakers, skipping")
                continue
            if not self.breakers[p].can_attempt():
                logger.warning(
                    json.dumps(
                        {
                            "event": "provider_skipped",
                            "provider": p,
                            "request_id": request_id,
                            "msg": "Circuit is OPEN",
                            "failures": self.breakers[p].failure_count,
                            "last_failure": self.breakers[p].last_failure_time,
                        }
                    )
                )
                continue

            try:
                result = await self._call_provider(
                    p, prompt, system_prompt, request_id, json_mode, rag_context
                )
                self.breakers[p].record_success()
                return {**result, "request_id": request_id, "provider": p}
            except Exception as e:
                self.breakers[p].record_failure()
                logger.error(
                    json.dumps(
                        {
                            "event": "provider_error",
                            "provider": p,
                            "error": str(e),
                            "request_id": request_id,
                        }
                    )
                )

        # Final Fallback logic if all providers fail
        logger.critical(
            json.dumps(
                {
                    "event": "hub_total_failure",
                    "request_id": request_id,
                    "msg": "All LLM providers exhausted or circuited",
                }
            )
        )
        raise RuntimeError(f"IntelligenceHub total failure for request {request_id}")

    def reset_circuit(self, provider: str):
        """Manually reset a provider's circuit breaker."""
        if provider in self.breakers:
            self.breakers[provider].reset()
            logger.info(f"Circuit breaker reset for provider: {provider}")

    def reset_all_circuits(self):
        """Reset all provider circuit breakers."""
        for provider, breaker in self.breakers.items():
            breaker.reset()
        logger.info("All provider circuits reset")

    def _route_complexity(self, complexity: str) -> str:
        """Determines the best provider based on task complexity (Economic Optimization)."""
        if complexity == "low":
            return "ollama"  # Local/Zero Cost
        if complexity == "medium":
            # Prefer Gemini (Cost-effective) or Groq (Fast)
            if self.google_key:
                return "gemini"
            if self.groq_key:
                return "groq"
            return "ollama"
        if complexity == "high":
            # Premium reasoning
            if self.openai_key:
                return "openai"
            if self.google_key:
                return "gemini"
            return "ollama"
        return "ollama"

    async def _call_provider(
        self, provider: str, prompt: str, system: str, rid: str, json_mode: bool, rag_context: str | None = None
    ) -> dict[str, Any]:
        if provider == "ollama":
            return await self._call_ollama(prompt, system, rid, json_mode, rag_context)
        elif provider == "openai":
            return await self._call_openai(prompt, system, rid, json_mode, rag_context)
        elif provider == "groq":
            return await self._call_groq(prompt, system, rid, json_mode, rag_context)
        elif provider == "gemini":
            return await self._call_gemini(prompt, system, rid, json_mode, rag_context)
        elif provider == "vllm":
            return await self._call_vllm(prompt, system, rid, json_mode, rag_context)
        raise ValueError(f"Unknown provider: {provider}")

    async def _call_ollama(
        self, prompt: str, system: str, rid: str, json_mode: bool, rag_context: str | None = None
    ) -> dict[str, Any]:
        url = self.ollama_url
        
        # Standard: RAG Context Injection
        effective_prompt = prompt
        if rag_context:
            effective_prompt = f"Relevant Context:\n{rag_context}\n\nTask:\n{prompt}"
            logger.info(f"[{rid}] Knowledge context injected into Ollama request.")

        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": effective_prompt},
            ],
            "stream": False,
            "options": {"temperature": 0.7, "num_predict": 1000},
        }
        if json_mode:
            payload["format"] = "json"

        # Standard: Dynamic Timeout for RAG operations (600s vs 300s)
        timeout = 600 if rag_context else 300
        
        async def _try_post(url):
            async with httpx.AsyncClient(timeout=timeout) as client:
                headers = {"X-Request-ID": rid}
                return await client.post(url, json=payload, headers=headers)

        try:
            start = time.time()
            resp = await _try_post(self.ollama_url)
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            if self.ollama_url != self.fallback_ollama_url:
                logger.warning(f"Ollama primary failed ({str(e)}), trying fallback: {self.fallback_ollama_url}")
                self.ollama_url = self.fallback_ollama_url
                start = time.time()
                resp = await _try_post(self.ollama_url)
            else:
                raise

        latency = time.time() - start

        if resp.status_code != 200:
            raise RuntimeError(f"Ollama error {resp.status_code}: {resp.text}")

        data = resp.json()
        content = data["message"]["content"]

        return {
            "response": content,
            "latency_sec": latency,
            "usage": {
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
                "total_tokens": data.get("prompt_eval_count", 0)
                + data.get("eval_count", 0),
            },
        }

    async def _call_openai(
        self, prompt: str, system: str, rid: str, json_mode: bool, rag_context: str | None = None
    ) -> dict[str, Any]:
        if not self.openai_key:
            raise ValueError("OpenAI key missing")

        # Standard: RAG Context Injection
        effective_prompt = prompt
        if rag_context:
            effective_prompt = f"Relevant Context:\n{rag_context}\n\nTask:\n{prompt}"

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_key.strip()}",
            "Content-Type": "application/json",
            "X-Request-ID": rid,
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": effective_prompt},
            ],
            "max_tokens": 1000,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=30) as client:
            start = time.time()
            resp = await client.post(url, headers=headers, json=payload)
            latency = time.time() - start

            if resp.status_code != 200:
                if resp.status_code == 429:
                    raise RuntimeError(
                        f"OpenAI error 429: Insufficient Quota or Rate Limit"
                    )
                raise RuntimeError(f"OpenAI error {resp.status_code}: {resp.text}")

            data = resp.json()
            content = data["choices"][0]["message"]["content"]

            return {
                "response": content,
                "latency_sec": latency,
                "usage": data.get("usage", {}),
            }

    async def _call_groq(
        self, prompt: str, system: str, rid: str, json_mode: bool, rag_context: str | None = None
    ) -> dict[str, Any]:
        if not self.groq_key:
            raise ValueError("Groq key missing")

        # Standard: RAG Context Injection
        effective_prompt = prompt
        if rag_context:
            effective_prompt = f"Relevant Context:\n{rag_context}\n\nTask:\n{prompt}"

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_key.strip()}",
            "Content-Type": "application/json",
            "X-Request-ID": rid,
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": effective_prompt},
            ],
            "max_tokens": 1000,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=20) as client:
            start = time.time()
            resp = await client.post(url, headers=headers, json=payload)
            latency = time.time() - start

            if resp.status_code != 200:
                raise RuntimeError(f"Groq error {resp.status_code}: {resp.text}")

            data = resp.json()
            content = data["choices"][0]["message"]["content"]

            return {
                "response": content,
                "latency_sec": latency,
                "usage": data.get("usage", {}),
            }

    async def _call_gemini(
        self, prompt: str, system: str, rid: str, json_mode: bool, rag_context: str | None = None
    ) -> dict[str, Any]:
        if not self.google_key:
            raise ValueError("Google/Gemini key missing")

        # Standard: RAG Context Injection
        effective_prompt = prompt
        if rag_context:
            effective_prompt = f"Relevant Context:\n{rag_context}\n\nTask:\n{prompt}"

        # Using the standard Google AI SDK or REST API
        # Let's use REST for zero-dependency consistency here
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.DEFAULT_VLM_MODEL}:generateContent?key={self.google_key.strip()}"

        headers = {"Content-Type": "application/json"}

        combined_prompt = f"System: {system}\n\nUser: {effective_prompt}"
        if json_mode:
            combined_prompt += "\n\nReturn ONLY a valid JSON object."

        payload = {
            "contents": [{"parts": [{"text": combined_prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1000,
            },
        }

        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        async with httpx.AsyncClient(timeout=60) as client:
            start = time.time()
            resp = await client.post(url, headers=headers, json=payload)
            latency = time.time() - start

            if resp.status_code != 200:
                raise RuntimeError(f"Gemini error {resp.status_code}: {resp.text}")

            data = resp.json()
            try:
                content = data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError) as e:
                raise RuntimeError(f"Gemini invalid response format: {data}")

            return {
                "response": content,
                "latency_sec": latency,
                "usage": {},  # Gemini REST doesn't always return usage in this format easily
            }

    async def _call_vllm(
        self, prompt: str, system: str, rid: str, json_mode: bool, rag_context: str | None = None
    ) -> dict[str, Any]:
        """vLLM provider (OpenAI compatible high-throughput inference)"""
        # Default to Ollama's OpenAI-compatible endpoint if not specified
        url = os.getenv("VLLM_URL", "http://ollama:11434/v1")
        if not url.endswith("/chat/completions"):
            url = f"{url.rstrip('/')}/chat/completions"
        
        effective_prompt = prompt
        if rag_context:
            effective_prompt = f"Relevant Context:\n{rag_context}\n\nTask:\n{prompt}"

        headers = {
            "Content-Type": "application/json",
            "X-Request-ID": rid,
        }
        payload = {
            "model": os.getenv("VLLM_MODEL", settings.OLLAMA_MODEL),
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": effective_prompt},
            ],
            "max_tokens": 1000,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=60) as client:
            start = time.time()
            resp = await client.post(url, headers=headers, json=payload)
            latency = time.time() - start

            if resp.status_code != 200:
                raise RuntimeError(f"vLLM error {resp.status_code}: {resp.text}")

            data = resp.json()
            content = data["choices"][0]["message"]["content"]

            return {
                "response": content,
                "latency_sec": latency,
                "usage": data.get("usage", {}),
            }


# Singleton accessor
base_intelligence_service = IntelligenceHub()
