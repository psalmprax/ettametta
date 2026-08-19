import pytest
import os
from src.services.llm.interpreter import interpreter_service

@pytest.mark.asyncio
async def test_interpreter_isolation():
    """Verify that the interpreter cannot access sensitive modules even if it tries."""
    # Ensure service is enabled for testing
    os.environ["ENABLE_INTERPRETER"] = "true"
    interpreter_service.enabled = True

    # Try to import os and run system command
    code = "import os; os.system('echo hacked')"
    result = await interpreter_service.execute_code(code)

    # It should fail because 'os' is not in safe_globals of the sandbox_runner
    # or because our keyword safeguard blocks it
    assert result["success"] is False
    assert "Forbidden keyword" in result["error"] or "name 'os' is not defined" in result["error"]

@pytest.mark.asyncio
async def test_native_effect_delegation():
    """Verify that generate_video_effect returns directions instead of code."""
    params = {"zoom_factor": 1.2}
    result = await interpreter_service.generate_video_effect("zoom", params)

    assert result["success"] is True
    assert "instruction" in result
    assert result["instruction"]["method"] == "apply_originality_transformation"
    assert result["instruction"]["params"]["zoom"] == 1.2
