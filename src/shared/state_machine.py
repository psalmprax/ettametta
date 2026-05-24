import logging
from enum import Enum
from typing import Any
from src.services.infrastructure.event_bus import base_event_service

logger = logging.getLogger("StateMachine")

class JobState(str, Enum):
    QUEUED = "QUEUED"
    PENDING = "PENDING"
    DISCOVERING = "DISCOVERY_ACTIVE"
    INGRESSING = "INGRESS_ACTIVE"
    COGNITION = "COGNITION_ACTIVE"
    SYNTHESIZING = "SYNTHESIS_ACTIVE"
    RENDERING = "RENDERING_ACTIVE"
    PUBLISHING = "PUBLISHING_ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class JobStateMachine:
    """
    Standard 1.1: Event-Driven State Machine for Video Job lifecycles.
    Ensures state transitions are published to the Event Bus for cross-service sync.
    """
    
    # Valid transitions: Current State -> List of Allowed Next States
    _TRANSITIONS = {
        JobState.PENDING: [JobState.DISCOVERING, JobState.INGRESSING, JobState.FAILED],
        JobState.DISCOVERING: [JobState.INGRESSING, JobState.FAILED],
        JobState.INGRESSING: [JobState.COGNITION, JobState.FAILED],
        JobState.COGNITION: [JobState.SYNTHESIZING, JobState.FAILED],
        JobState.SYNTHESIZING: [JobState.RENDERING, JobState.FAILED],
        JobState.RENDERING: [JobState.PUBLISHING, JobState.FAILED],
        JobState.PUBLISHING: [JobState.COMPLETED, JobState.FAILED],
        JobState.FAILED: [JobState.PENDING], # Allow retry
        JobState.COMPLETED: [] # Terminal
    }

    @classmethod
    async def transition_to(cls, job_id: str, current_state: JobState, next_state: JobState, metadata: dict[str, Any] | None = None):
        """
        Validates and publishes a state transition event.
        """
        if next_state not in cls._TRANSITIONS.get(current_state, []):
            logger.warning(f"⚠️ Illegal transition attempt for job {job_id}: {current_state} -> {next_state}")
            # We still permit it in 'relaxed' hardening phase but log it
        
        event_payload = {
            "job_id": job_id,
            "previous_state": current_state,
            "new_state": next_state,
            "metadata": metadata or {},
            "timestamp": None # Set by event bus
        }
        
        await base_event_service.emit("job.state_changed", event_payload)
        logger.info(f"🔄 [State] Job {job_id} transitioned: {current_state} -> {next_state}")

base_state_machine = JobStateMachine()
