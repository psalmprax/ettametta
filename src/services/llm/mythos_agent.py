import json
import logging
from typing import Any, List, Dict
from src.services.llm.intelligence_hub import IntelligenceHub

logger = logging.getLogger("MythosAgent")

class MythosReasoningAgent:
    """
    OpenMythos-inspired Reasoning Agent.
    Simulates Recurrent-Depth Reasoning through a Prelude-Recurrent-Coda protocol.
    """

    def __init__(self, hub: IntelligenceHub = None, provider: str = None):
        self.hub = hub or IntelligenceHub()
        self.provider = provider # Explicit provider override

    async def reason(self, prompt: str, depth: int = 3, provider: str = None) -> Dict[str, Any]:
        """
        Executes the Mythos Reasoning Protocol.
        1. Prelude: Encode input into initial latent observations.
        2. Recurrent: Iterate and refine latent state with input injection.
        3. Coda: Finalize output.
        """
        trace = []
        
        target_provider = provider or self.provider
        
        # --- PRELUDE ---
        logger.info(f"[Mythos] Entering Prelude (Provider: {target_provider or 'auto'}) for prompt: {prompt}")
        latent_state = await self._prelude(prompt, target_provider)
        trace.append({"stage": "prelude", "state": latent_state})

        # --- RECURRENT BLOCK ---
        for i in range(depth):
            logger.info(f"[Mythos] Recurrent Loop {i+1}/{depth} (Provider: {target_provider or 'auto'})")
            latent_state = await self._recurrent_step(prompt, latent_state, i+1, target_provider)
            trace.append({"stage": f"loop_{i+1}", "state": latent_state})

        # --- CODA ---
        logger.info(f"[Mythos] Entering Coda (Provider: {target_provider or 'auto'}) for finalization")
        final_answer = await self._coda(prompt, latent_state, target_provider)
        
        return {
            "answer": final_answer,
            "trace": trace,
            "depth": depth
        }

    async def _prelude(self, prompt: str, provider: str = None) -> str:
        """Encodes the initial input into a high-density reasoning state."""
        system = (
            "You are the OpenMythos Prelude Encoder. "
            "Your task is to extract the core logic, hidden constraints, and underlying 'mythos' of the user's input. "
            "Convert the input into a dense 'Latent Reasoning State'—a list of high-level abstractions and initial hypotheses."
        )
        user = f"Input: {prompt}\n\nGenerate initial Latent Reasoning State:"
        
        # If provider is specified, we might need a custom call pattern or just pass it to hub if it supported it.
        # IntelligenceHub.chat now supports a 'provider' override.
        res = await self.hub.chat(prompt=user, system_prompt=system, complexity="high", provider=provider)
        return res.get("response", "")

    async def _recurrent_step(self, original_input: str, current_state: str, step: int, provider: str = None) -> str:
        """
        Refines the reasoning state. 
        Uses 'Input Injection' (passing the original input) to prevent state drift.
        """
        system = (
            f"You are the OpenMythos Recurrent Block (Loop {step}). "
            "Your task is to refine, critique, and evolve the current Latent Reasoning State. "
            "Compare the current state against the Original Input (Input Injection) to ensure no drift occurs. "
            "Deepen the reasoning, resolve contradictions, and 'think' through the implications."
        )
        user = (
            f"Original Input: {original_input}\n\n"
            f"Current Latent State: {current_state}\n\n"
            "Produce the Evolved Latent State:"
        )
        
        res = await self.hub.chat(prompt=user, system_prompt=system, complexity="high", provider=provider)
        return res.get("response", "")

    async def _coda(self, original_input: str, final_state: str, provider: str = None) -> str:
        """Decodes the final matured reasoning state into a user-facing response."""
        system = (
            "You are the OpenMythos Coda Decoder. "
            "Your task is to take the matured Latent Reasoning State and the Original Input, "
            "and synthesize the final, definitive response for the user. "
            "The response should be clear, authoritative, and reflect the depth of the reasoning process."
        )
        user = (
            f"Original Input: {original_input}\n\n"
            f"Matured Latent State: {final_state}\n\n"
            "Final Response:"
        )
        
        res = await self.hub.chat(prompt=user, system_prompt=system, complexity="high", provider=provider)
        return res.get("response", "")
