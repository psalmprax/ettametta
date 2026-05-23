import pytest
from unittest.mock import AsyncMock, patch
from src.shared.state_machine import JobStateMachine, JobState

@pytest.mark.asyncio
async def test_state_machine_transitions():
    with patch("src.shared.state_machine.base_event_service") as mock_event_service:
        mock_event_service.emit = AsyncMock()

        # Test valid transition: None -> FAILED
        await JobStateMachine.transition_to("test-job-1", None, JobState.FAILED)
        mock_event_service.emit.assert_called_once_with(
            "job.state_changed",
            {
                "job_id": "test-job-1",
                "previous_state": None,
                "new_state": JobState.FAILED,
                "metadata": {},
                "timestamp": None,
            }
        )
        mock_event_service.emit.reset_mock()

        # Test valid transition: QUEUED -> PENDING
        await JobStateMachine.transition_to("test-job-2", JobState.QUEUED, JobState.PENDING)
        mock_event_service.emit.assert_called_once_with(
            "job.state_changed",
            {
                "job_id": "test-job-2",
                "previous_state": JobState.QUEUED,
                "new_state": JobState.PENDING,
                "metadata": {},
                "timestamp": None,
            }
        )
        mock_event_service.emit.reset_mock()

        # Test invalid transition: PENDING -> RENDERING
        with pytest.raises(ValueError) as excinfo:
            await JobStateMachine.transition_to("test-job-3", JobState.PENDING, JobState.RENDERING)
        assert "Illegal state transition" in str(excinfo.value)
        mock_event_service.emit.assert_not_called()
