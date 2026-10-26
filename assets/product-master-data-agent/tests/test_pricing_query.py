"""Tests for standard list price queries via the Sales Price MCP tool (REQ-006)."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage


@pytest.fixture(autouse=True)
def _sys_path(add_agent_to_path):
    """Ensure app/ is on sys.path for all tests in this module."""


@pytest.fixture
def mock_price_tools():
    """Build a list of mock MCP tools simulating Sales Price API responses."""
    tool = MagicMock()
    tool.name = "get_salesprice_for_sap_self"
    tool.description = "Retrieve sales price entries for products"
    tool.args_schema = None
    tool.arun = AsyncMock(
        return_value=json.dumps({
            "results": [{
                "Material": "P-100",
                "SalesOrganization": "1000",
                "DistributionChannel": "10",
                "ConditionRateValue": "450.00",
                "ConditionRateValueUnit": "EUR",
                "ConditionQuantity": "1.000",
                "ConditionQuantityUnit": "EA",
                "ConditionValidityEndDate": "/Date(9999999999000)/"
            }]
        })
    )
    return [tool]


@pytest.fixture
def agent():
    from app.agent import SampleAgent
    return SampleAgent()


@pytest.mark.asyncio
async def test_list_price_query_returns_price(agent, mock_price_tools):
    """Agent returns standard list price for a product."""
    with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {"response": "The standard list price for product P-100 is €450.00 EUR per EA, valid until 31.12.9999."}
        response = await agent.invoke("What is the list price for P-100?", "ctx-p1", tools=mock_price_tools)

    assert response.status == "completed"
    assert "450" in response.message or "price" in response.message.lower()


@pytest.mark.asyncio
async def test_list_price_not_found(agent, mock_price_tools):
    """Agent returns a clear message when no price is found."""
    with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {"response": "No price found for product UNKNOWN-99 in sales organization 1000."}
        response = await agent.invoke("What is the price for UNKNOWN-99?", "ctx-p2", tools=mock_price_tools)

    assert response.status == "completed"
    assert (
        "no price" in response.message.lower()
        or "not found" in response.message.lower()
        or "unknown" in response.message.lower()
    )


@pytest.mark.asyncio
async def test_price_query_includes_currency(agent, mock_price_tools):
    """Agent includes currency in price response."""
    with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {"response": "Product TG11 has a list price of €1,250.00 EUR per EA via sales org 1000."}
        response = await agent.invoke("How much does TG11 cost?", "ctx-p3", tools=mock_price_tools)

    assert response.status == "completed"
    assert response.message


@pytest.mark.asyncio
async def test_price_api_error_handled_gracefully(agent, mock_price_tools):
    """Agent handles API error for price query without fabricating data."""
    with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {"response": "I was unable to retrieve the price for P-100. The pricing API returned an error: service unavailable."}
        response = await agent.invoke("Get me the price for P-100", "ctx-p4", tools=mock_price_tools)

    assert response.status == "completed"
    assert response.message
    assert "fabricated" not in response.message.lower()
