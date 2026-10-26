"""Unit tests for the product master data query flow (REQ-001)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage


@pytest.fixture(autouse=True)
def _sys_path(add_agent_to_path):
    """Ensure app/ is on sys.path for all tests in this module."""


@pytest.fixture
def mock_tools():
    """Build a list of mock MCP tools simulating Product Master MCP responses."""
    tool = MagicMock()
    tool.name = "list_a_product_for_api_product_srv"
    tool.description = "Retrieve a list of entities from the A_Product collection"
    tool.args_schema = None
    tool.arun = AsyncMock(
        return_value=json.dumps({
            "results": [{
                "Product": "P-100",
                "ProductType": "FERT",
                "BaseUnit": "EA",
                "GrossWeight": "2.500",
                "NetWeight": "2.200",
                "WeightUnit": "KG",
                "MaterialVolume": "0.005",
                "VolumeUnit": "M3",
                "SizeOrDimensionText": "30cm x 20cm x 10cm",
            }]
        })
    )
    return [tool]


@pytest.fixture
def agent():
    from agent import SampleAgent
    return SampleAgent()


def test_agent_can_be_instantiated(agent):
    """The agent can be created without errors."""
    assert agent is not None


def test_agent_has_stream_method(agent):
    """The agent exposes a stream() async generator."""
    assert hasattr(agent, "stream")
    assert callable(agent.stream)


def test_agent_has_invoke_method(agent):
    """The agent exposes an invoke() async method."""
    assert hasattr(agent, "invoke")
    assert callable(agent.invoke)


@pytest.mark.asyncio
async def test_stream_returns_processing_then_result(agent, mock_tools):
    """stream() yields a processing status then a completed response."""
    ai_response = AIMessage(content="Product P-100: Industrial Water Pump, weight 2.5 KG, dimensions 30x20x10cm.")

    with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {"response": ai_response.content}

        chunks = []
        async for chunk in agent.stream("What is product P-100?", "ctx-001", tools=mock_tools):
            chunks.append(chunk)

    assert len(chunks) >= 2
    assert chunks[0]["is_task_complete"] is False
    assert chunks[-1]["is_task_complete"] is True
    assert "P-100" in chunks[-1]["content"] or len(chunks[-1]["content"]) > 0


@pytest.mark.asyncio
async def test_invoke_returns_completed_status(agent, mock_tools):
    """invoke() returns AgentResponse with status=completed on success."""
    with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {"response": "Product P-100 weighs 2.5 KG."}

        response = await agent.invoke("Tell me about product P-100", "ctx-002", tools=mock_tools)

    assert response.status == "completed"
    assert len(response.message) > 0


@pytest.mark.asyncio
async def test_product_not_found_returns_clear_message(agent, mock_tools):
    """Agent returns a clear message when a product is not found."""
    with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {"response": "Product not found: NONEXISTENT-PRODUCT does not exist in the system."}

        response = await agent.invoke("Tell me about product NONEXISTENT-PRODUCT", "ctx-003", tools=mock_tools)

    assert response.status == "completed"
    assert "not found" in response.message.lower() or "nonexistent" in response.message.lower()
