import os
import asyncio
import json
import logging
import time
import httpx
from typing import Any
from uuid import uuid4
from api.config import settings

# Configure Structured Logging (Standard 2.22)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IntelligenceHub")

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
        self.state = "CLOSED" # CLOSED, OPEN, HALF_OPEN

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        logger.warning(json.dumps({
            "event": "circuit_breaker_failure",
            "name": self.name,
            "failure_count": self.failure_count,
            "threshold": self.failure_threshold,
            "state": self.state
        }))
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(json.dumps({
                "event": "circuit_breaker_open",
                "name": self.name,
                "msg": f"Circuit breaker {self.name} is now OPEN"
            }))

    def record_success(self):
        if self.state != "CLOSED":
            logger.info(json.dumps({
                "event": "circuit_breaker_closed",
                "name": self.name,
                "msg": f"Circuit breaker {self.name} is now CLOSED"
            }))
        self.failure_count = 0
        self.state = "CLOSED"

    def can_attempt(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
        if self.state == "HALF_OPEN":
            return True
        return False

class IntelligenceHub:
    """
    Unified Intelligence Model (Tier 10.0)
    Centralizes all LLM traffic with failover and hardening.
    """
    
    def __init__(self):
        self.openai_key = settings.OPENAI_API_KEY
        self.groq_key = settings.GROQ_API_KEY
        
        # Hardening: Dedicated Circuit Breakers per provider
        self.breakers = {
            "openai": CircuitBreaker("OpenAI-Champion"),
            "groq": CircuitBreaker("Groq-Challenger")
        }
        
        # Primary/Champion configuration
        self.primary_provider = "openai"
        self.fallback_provider = "groq"
        
    async def chat(
        self, 
        prompt: str, 
        system_prompt: str = "You are a Viral Narrative Analyst.",
        session_id: str | None = None,
        json_mode: bool = False
    ) -> dict[str, Any]:
        """
        Unified chat interface with failure persistence (Standard 3.25)
        """
        request_id = session_id or str(uuid4())
        
        # Define candidates in order (Champion -> Challenger)
        candidates = [self.primary_provider, self.fallback_provider]
        
        for provider in candidates:
            if not self.breakers[provider].can_attempt():
                logger.warning(json.dumps({
                    "event": "provider_skipped",
                    "provider": provider,
                    "request_id": request_id,
                    "msg": "Circuit is OPEN"
                }))
                continue
            
            try:
                result = await self._call_provider(provider, prompt, system_prompt, request_id, json_mode)
                self.breakers[provider].record_success()
                return {**result, "request_id": request_id, "provider": provider}
            except Exception as e:
                self.breakers[provider].record_failure()
                logger.error(json.dumps({
                    "event": "provider_error",
                    "provider": provider,
                    "error": str(e),
                    "request_id": request_id
                }))
                
        # Final Fallback logic if all providers fail
        logger.critical(json.dumps({
            "event": "hub_total_failure",
            "request_id": request_id,
            "msg": "All LLM providers exhausted or circuited"
        }))
        raise RuntimeError(f"IntelligenceHub total failure for request {request_id}")

    async def _call_provider(self, provider: str, prompt: str, system: str, rid: str, json_mode: bool) -> dict[str, Any]:
        if provider == "openai":
            return await self._call_openai(prompt, system, rid, json_mode)
        elif provider == "groq":
            return await self._call_groq(prompt, system, rid, json_mode)
        raise ValueError(f"Unknown provider: {provider}")

    async def _call_openai(self, prompt: str, system: str, rid: str, json_mode: bool) -> dict[str, Any]:
        if not self.openai_key: raise ValueError("OpenAI key missing")
        
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_key.strip()}",
            "Content-Type": "application/json",
            "X-Request-ID": rid
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=30) as client:
            start = time.time()
            resp = await client.post(url, headers=headers, json=payload)
            latency = time.time() - start
            
            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI error {resp.status_code}: {resp.text}")
            
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            
            return {
                "response": content,
                "latency_sec": latency,
                "usage": data.get("usage", {})
            }

    async def _call_groq(self, prompt: str, system: str, rid: str, json_mode: bool) -> dict[str, Any]:
        if not self.groq_key: raise ValueError("Groq key missing")
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_key.strip()}",
            "Content-Type": "application/json",
            "X-Request-ID": rid
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000
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
                "usage": data.get("usage", {})
            }

# Singleton accessor
base_intelligence_hub = IntelligenceHub()
