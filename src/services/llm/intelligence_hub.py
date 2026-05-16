import os
import asyncio
import json
import logging
import time
import httpx
from typing import Any
from uuid import uuid4
from src.api.config import settings
from src.api.utils.tracing import get_request_id
from src.api.utils.resilience import CircuitBreaker
from opentelemetry import trace
from src.shared.observability import get_logger

# Configure Structured Logging (Standard 2.22)
logger = get_logger("IntelligenceHub")
tracer = trace.get_tracer(__name__)



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

        # Dynamic Load Balancer: Track health per provider
        self.provider_health = {
            p: {"errors": 0, "last_error": 0, "status": "healthy"}
            for p in ["ollama", "openai", "groq", "gemini", "vllm", "dify"]
        }

        # Hardening: Dedicated Circuit Breakers per provider
        self.breakers = {
            "ollama": CircuitBreaker(name="Ollama-Local-Edge"),
            "openai": CircuitBreaker(name="OpenAI-Champion"),
            "groq": CircuitBreaker(name="Groq-Challenger"),
            "gemini": CircuitBreaker(name="Gemini-Titan"),
            "vllm": CircuitBreaker(name="vLLM-Production-Edge"),
            "dify": CircuitBreaker(name="Dify-Orchestrator"),
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
        timeout_seconds: int | None = None,  # Global safety-net timeout (None uses settings)
    ) -> dict[str, Any]:
        """
        Unified chat interface with complexity-based routing and failure persistence.
        Instrumented with OpenTelemetry for end-to-end tracing.
        """
        with tracer.start_as_current_span("IntelligenceHub.chat") as span:
            request_id = session_id or str(uuid4())
            span.set_attribute("request_id", request_id)
            span.set_attribute("complexity", complexity)
            if provider:
                span.set_attribute("provider_override", provider)

            actual_timeout = timeout_seconds or settings.LLM_TIMEOUT * 10
            try:
                result = await asyncio.wait_for(
                    self._chat_inner(
                        prompt, system_prompt, request_id, json_mode,
                        complexity, provider, rag_context
                    ),
                    timeout=actual_timeout,
                )
                span.set_attribute("provider_used", result.get("provider", "unknown"))
                return result
            except asyncio.TimeoutError:
                logger.critical(
                    json.dumps(
                        {
                            "event": "hub_global_timeout",
                            "request_id": request_id,
                            "timeout_seconds": actual_timeout,
                            "msg": f"Global timeout ({actual_timeout}s) exceeded",
                        }
                    )
                )
                span.set_status(trace.Status(trace.StatusCode.ERROR, "Global Timeout"))
                raise RuntimeError(f"IntelligenceHub global timeout for request {request_id}")
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise

    async def _chat_inner(
        self,
        prompt: str,
        system_prompt: str,
        session_id: str | None,
        json_mode: bool,
        complexity: str,
        provider: str | None,
        rag_context: str | None,
    ) -> dict[str, Any]:
        """Inner implementation of chat, wrapped by the global timeout in chat()."""
        request_id = session_id or get_request_id()

        # Step 1: Route based on complexity
        primary = self._route_complexity(complexity)
        
        # Step 2: Define candidates (Primary -> Fallbacks)
        if provider:
            p_norm = provider.lower()
            if p_norm == "google":
                p_norm = "gemini"
            candidates = [p_norm]
        else:
            candidates = [primary, "ollama", "dify", "vllm", "gemini", "groq", "openai"]
        
        # Remove duplicates while preserving order
        candidates = list(dict.fromkeys(candidates))
        logger.info(f"[{request_id}] LLM Candidates: {candidates}")

        for p in candidates:
            if p not in self.breakers:
                logger.warning(f"Provider {p} not in breakers, skipping")
                continue
            if self.provider_health[p]["status"] != "healthy":
                last_error_time = self.provider_health[p]["last_error"]
                # Auto-heal after 10 minutes
                if time.time() - last_error_time > 600:
                    self.provider_health[p]["status"] = "healthy"
                    self.provider_health[p]["errors"] = 0
                    logger.info(f"Provider {p} auto-healed after timeout")
                else:
                    logger.warning(f"Provider {p} is {self.provider_health[p]['status']}, skipping")
                    continue

            if self.breakers[p].is_open():
                logger.warning(
                    json.dumps(
                        {
                            "event": "provider_skipped",
                            "provider": p,
                            "request_id": request_id,
                            "msg": "Circuit is OPEN",
                        }
                    )
                )
                continue

            try:
                logger.info(f"Attempting provider {p} for request {request_id}")
                with tracer.start_as_current_span(f"IntelligenceHub._call_{p}") as subspan:
                    subspan.set_attribute("provider", p)
                    result = await self._call_provider(
                        p, prompt, system_prompt, request_id, json_mode, rag_context
                    )
                    self.breakers[p].record_success()
                    # Reset health on success
                    self.provider_health[p]["errors"] = 0
                    self.provider_health[p]["status"] = "healthy"
                    return {**result, "request_id": request_id, "provider": p}
            except Exception as e:
                logger.debug(f"Provider {p} failed: {e}")
                self.breakers[p].record_failure()
                
                # Record health failure
                self.provider_health[p]["errors"] += 1
                self.provider_health[p]["last_error"] = time.time()
                if "429" in str(e) or "quota" in str(e).lower():
                    self.provider_health[p]["status"] = "rate_limited"
                elif self.provider_health[p]["errors"] >= 3:
                    self.provider_health[p]["status"] = "degraded"

                logger.error(
                    json.dumps(
                        {
                            "event": "provider_error",
                            "provider": p,
                            "error": str(e),
                            "request_id": request_id,
                            "health_status": self.provider_health[p]["status"]
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
            if settings.DIFY_API_KEY:
                return "dify"
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
        elif provider == "dify":
            return await self._call_dify(prompt, system, rid, json_mode, rag_context)
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
            "options": {"temperature": 0.7, "num_predict": 4096},
        }
        if json_mode:
            payload["format"] = "json"

        # Standard: Dynamic Timeout for RAG operations (120s vs 90s)
        # Kept tight to prevent Nexus jobs hanging in COMPOSING state
        timeout = settings.LLM_TIMEOUT * 2 # Standard: 2x base timeout for local Ollama
        
        async def _try_post(url):
            async with httpx.AsyncClient(timeout=timeout) as client:
                headers = {"X-Request-ID": rid}
                return await client.post(url, json=payload, headers=headers)

        try:
            logger.info(f"[{rid}] Calling Ollama at {self.ollama_url} with model {settings.OLLAMA_MODEL}")
            start = time.time()
            resp = await _try_post(self.ollama_url)
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            if self.ollama_url != self.fallback_ollama_url:
                logger.warning(f"Ollama primary failed ({str(e)}), trying fallback: {self.fallback_ollama_url}")
                self.ollama_url = self.fallback_ollama_url
                start = time.time()
                resp = await _try_post(self.ollama_url)
            else:
                raise

        latency = time.time() - start

        logger.debug(f"Ollama Status: {resp.status_code}")
        if resp.status_code != 200:
            raise RuntimeError(f"Ollama error {resp.status_code}: {resp.text}")

        logger.debug("Parsing Ollama JSON body...")
        data = resp.json()
        logger.debug("Ollama JSON parsed successfully.")
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

        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
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

        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
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

    async def _call_dify(
        self, prompt: str, system: str, rid: str, json_mode: bool, rag_context: str | None = None
    ) -> dict[str, Any]:
        """Dify AI Orchestrator provider"""
        from src.services.llm.dify_client import base_dify_client
        
        effective_prompt = prompt
        if rag_context:
            effective_prompt = f"Relevant Context:\n{rag_context}\n\nTask:\n{prompt}"
            
        # Combine system and user prompt for Dify query
        query = f"Instruction: {system}\n\nInput: {effective_prompt}"
        
        start = time.time()
        try:
            # We use chat_messages by default for the orchestrator
            response = await base_dify_client.chat_messages(
                query=query,
                user_id=f"ettametta_{rid}",
                inputs={"json_mode": json_mode}
            )
            latency = time.time() - start
            
            content = response.get("answer", "")
            
            # Metadata for tracing
            usage = {
                "total_tokens": 0,
            }
            if "metadata" in response and "usage" in response["metadata"]:
                usage = response["metadata"]["usage"]

            return {
                "response": content,
                "latency_sec": latency,
                "usage": usage,
                "conversation_id": response.get("conversation_id"),
                "message_id": response.get("id")
            }
        except Exception as e:
            logger.error(f"Dify provider call failed: {e}")
            raise


# Singleton accessor
base_intelligence_service = IntelligenceHub()
