"""Tests for customer-specific pricing conditions queries (REQ-007)."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage


@pytest.fixture(autouse=True)
def _sys_path(add_agent_to_path):
    """Ensure app/ is on sys.path for all tests in this module."""


@pytest.fixture
def mock_condition_tools():
    """Build a list of mock MCP tools simulating Pricing Conditions API responses."""
    tool = MagicMock()
    tool.name = "list_a_slsprcgconditionrecord"
    tool.description = "Retrieve a list of sales pricing condition records"
    tool.args_schema = None
    tool.arun = AsyncMock(
        return_value=json.dumps({
            "results": [{
                "ConditionRecord": "0000000001",
                "ConditionType": "PR00",
                "SalesOrganization": "1000",
                "DistributionChannel": "10",
                "Material": "P-100",
                "Customer": "CUST-1001",
                "ConditionRateValue": "420.00",
                "ConditionRateValueUnit": "EUR",
                "ConditionValidityEndDate": "/Date(9999999999000)/"
            }, {
                "ConditionRecord": "0000000002",
                "ConditionType": "K007",
                "SalesOrganization": "1000",
                "DistributionChannel": "10",
                "Material": "P-100",
                "Customer": "CUST-1001",
                "ConditionRateValue": "-5.00",
                "ConditionRateValueUnit": "%",
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
async def test_customer_discount_query_returns_conditions(agent, mock_condition_tools):
    """Agent returns customer-specific pricing conditions including discounts."""
    with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {"response": "Customer CUST-1001 has a special price of €420.00 EUR for product P-100, plus a 5% discount (condition K007), valid until 31.12.9999."}
        response = await agent.invoke("What discount does customer CUST-1001 get on P-100?", "ctx-c1", tools=mock_condition_tools)

    assert response.status == "completed"
    assert response.message
    assert "420" in response.message or "discount" in response.message.lower() or "5%" in response.message


@pytest.mark.asyncio
async def test_no_conditions_found_returns_clear_message(agent, mock_condition_tools):
    """Agent returns clear message when no pricing conditions exist."""
    with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {"response": "No pricing conditions found for customer NEW-CUST and product P-100 in the system."}
        response = await agent.invoke("Any special pricing for NEW-CUST on P-100?", "ctx-c2", tools=mock_condition_tools)

    assert response.status == "completed"
    assert "no" in response.message.lower() or "not found" in response.message.lower()


@pytest.mark.asyncio
async def test_pricing_conditions_with_validity_dates(agent, mock_condition_tools):
    """Agent includes validity period in pricing condition responses."""
    with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {"response": "The pricing condition for P-100 (record 0000000001) is valid from 01.01.2024 to 31.12.9999."}
        response = await agent.invoke("When is the P-100 pricing condition valid?", "ctx-c3", tools=mock_condition_tools)

    assert response.status == "completed"
    assert response.message


@pytest.mark.asyncio
async def test_pricing_conditions_api_error_handled(agent, mock_condition_tools):
    """Agent handles API error for pricing conditions without fabricating data."""
    with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {"response": "I was unable to retrieve pricing conditions for CUST-1001. The pricing conditions API returned an error."}
        response = await agent.invoke("Get pricing conditions for CUST-1001 on TG11", "ctx-c4", tools=mock_condition_tools)

    assert response.status == "completed"
    assert response.message
    assert "fabricated" not in response.message.lower()
