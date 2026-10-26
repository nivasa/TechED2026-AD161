"""Unit tests for 'product not found' scenario — REQ-001 acceptance criteria."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _sys_path(add_agent_to_path):
    """Ensure app/ is on sys.path for all tests in this module."""


@pytest.fixture
def agent():
    from agent import SampleAgent
    return SampleAgent()


@pytest.fixture
def empty_result_tool():
    """Mock tool that returns empty results — simulating product not found."""
    tool = MagicMock()
    tool.name = "list_a_product_for_api_product_srv"
    tool.description = "Retrieve product master data"
    tool.args_schema = None
    tool.arun = AsyncMock(return_value='{"results": []}')
    return [tool]


@pytest.mark.asyncio
async def test_not_found_returns_clear_message(agent, empty_result_tool):
    """When a product does not exist, agent returns a 'not found' message."""
    with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {
            "response": "Product not found: I could not find any product matching 'FAKE-001' in S/4HANA."
        }

        response = await agent.invoke(
            "Tell me about product FAKE-001",
            "ctx-nf-001",
            tools=empty_result_tool,
        )

    assert response.status == "completed"
    assert "not found" in response.message.lower() or "could not find" in response.message.lower()


@pytest.mark.asyncio
async def test_not_found_does_not_fabricate_data(agent, empty_result_tool):
    """Agent must not return made-up product data when no results are returned."""
    with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {
            "response": "I could not find product FAKE-001 in the SAP system. Please verify the product ID."
        }

        response = await agent.invoke(
            "What is the weight of product FAKE-001?",
            "ctx-nf-002",
            tools=empty_result_tool,
        )

    assert response.status == "completed"
    # Response should NOT contain made-up weight values like "2.5 KG" for a non-existent product
    assert response.message is not None
    assert len(response.message) > 0


@pytest.mark.asyncio
async def test_invalid_product_id_format_handled(agent, empty_result_tool):
    """Agent handles malformed or empty product IDs gracefully."""
    with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {
            "response": "I need a valid product ID to look up product information. Could you please provide the product number?"
        }

        response = await agent.invoke(
            "What is the weight of product ???",
            "ctx-nf-003",
            tools=empty_result_tool,
        )

    assert response.status == "completed"
    assert len(response.message) > 0
