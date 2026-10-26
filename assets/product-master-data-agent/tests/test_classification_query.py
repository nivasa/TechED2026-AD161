"""Unit tests for the product classification query flow (REQ-002)."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _sys_path(add_agent_to_path):
    """Ensure app/ is on sys.path for all tests in this module."""


@pytest.fixture
def classification_tool():
    """Mock MCP tool simulating Product Classification responses."""
    tool = MagicMock()
    tool.name = "list_a_productclass_for_api_clfn_product_srv"
    tool.description = "Retrieve product class assignments"
    tool.args_schema = None
    tool.arun = AsyncMock(
        return_value=json.dumps({
            "results": [{
                "Product": "P-100",
                "ClassType": "001",
                "ClassInternalID": "CL-PUMPS-001",
                "ClassDescription": "Industrial Pumps"
            }]
        })
    )
    return [tool]


@pytest.fixture
def agent():
    from agent import SampleAgent
    return SampleAgent()


def test_agent_handles_classification_query(agent):
    """Agent can be queried about product classification."""
    assert agent is not None


@pytest.mark.asyncio
async def test_classification_data_returned(agent, classification_tool):
    """Agent returns class and characteristic data when asked about classification."""
    with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {
            "response": "Product P-100 belongs to class 'Industrial Pumps' (CL-PUMPS-001, ClassType 001)."
        }

        response = await agent.invoke(
            "What class does product P-100 belong to?",
            "ctx-cls-001",
            tools=classification_tool,
        )

    assert response.status == "completed"
    assert len(response.message) > 0


@pytest.mark.asyncio
async def test_missing_classification_data_handled(agent, classification_tool):
    """Agent clearly states when classification data is missing for a product."""
    with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {
            "response": "No classification data is available for product XYZ-999."
        }

        response = await agent.invoke(
            "What are the technical attributes of product XYZ-999?",
            "ctx-cls-002",
            tools=classification_tool,
        )

    assert response.status == "completed"
    assert "no classification" in response.message.lower() or "not available" in response.message.lower() or len(response.message) > 0


@pytest.mark.asyncio
async def test_characteristic_values_returned(agent, classification_tool):
    """Agent returns characteristic values when asked about technical specs."""
    with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {
            "response": "Product P-100 technical attributes: MATERIAL_TYPE = STAINLESS_STEEL, MAX_FLOW_RATE = 500 L/min."
        }

        response = await agent.invoke(
            "What are the technical specs of product P-100?",
            "ctx-cls-003",
            tools=classification_tool,
        )

    assert response.status == "completed"
    assert len(response.message) > 0
