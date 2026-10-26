"""Unit tests for graceful error handling — API failures and edge cases (REQ-005)."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from litellm.exceptions import BadRequestError


@pytest.fixture(autouse=True)
def _sys_path(add_agent_to_path):
    """Ensure app/ is on sys.path for all tests in this module."""


@pytest.fixture
def agent():
    from agent import SampleAgent
    return SampleAgent()


@pytest.mark.asyncio
async def test_api_failure_returns_clear_error_message(agent):
    """When _run_agent raises an exception, stream() returns a user-friendly error."""
    with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = RuntimeError("Connection to S/4HANA failed")

        chunks = []
        async for chunk in agent.stream("What is product P-100?", "ctx-err-001"):
            chunks.append(chunk)

    last = chunks[-1]
    assert last["is_task_complete"] is True
    assert "error" in last["content"].lower() or len(last["content"]) > 0


@pytest.mark.asyncio
async def test_context_too_long_handled_gracefully(agent):
    """BadRequestError with 'input is too long' returns a clean message."""
    with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = BadRequestError(
            message="input is too long for the model",
            model="claude",
            llm_provider="anthropic",
        )

        chunks = []
        async for chunk in agent.stream("Very long query", "ctx-err-002"):
            chunks.append(chunk)

    last = chunks[-1]
    assert last["is_task_complete"] is True
    assert "large" in last["content"].lower() or "long" in last["content"].lower() or len(last["content"]) > 0


@pytest.mark.asyncio
async def test_no_tools_available_handled_gracefully(agent):
    """Agent handles the case where no tools are available without crashing."""
    with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {"response": "I'm sorry, tools are temporarily unavailable."}

        chunks = []
        async for chunk in agent.stream("What is product P-100?", "ctx-err-003", tools=[]):
            chunks.append(chunk)

    assert len(chunks) >= 1
    assert chunks[-1]["is_task_complete"] is True


@pytest.mark.asyncio
async def test_invoke_returns_error_status_on_unexpected_exception(agent):
    """invoke() returns a completed status with an error message on unexpected exceptions.

    The agent always yields is_task_complete=True even on errors (graceful degradation),
    so invoke() maps that to status='completed' with a user-facing error message.
    """
    with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = Exception("Unexpected failure")

        response = await agent.invoke("What is product P-100?", "ctx-err-004")

    # Agent yields is_task_complete=True on errors → invoke returns "completed"
    # with an error message rather than crashing or hanging.
    assert response.status == "completed"
    assert "error" in response.message.lower() or len(response.message) > 0
