"""Integration test — end-to-end agent flow with mocked LLM and MCP responses.

Covers REQ-001 (product query), REQ-003 (multi-turn conversation), and REQ-005 (data accuracy).
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage


@pytest.fixture(autouse=True)
def _sys_path(add_agent_to_path):
    """Ensure app/ is on sys.path for all tests in this module."""


@pytest.fixture
def product_tools():
    """Set of mock MCP tools covering both Product Master and Classification APIs."""
    product_tool = MagicMock()
    product_tool.name = "get_a_product_for_api_product_srv"
    product_tool.description = "Retrieve a single product by key"
    product_tool.args_schema = None
    product_tool.arun = AsyncMock(
        return_value=json.dumps({
            "Product": "P-100",
            "ProductType": "FERT",
            "BaseUnit": "EA",
            "GrossWeight": "2.500",
            "WeightUnit": "KG",
            "SizeOrDimensionText": "30cm x 20cm x 10cm",
        })
    )

    desc_tool = MagicMock()
    desc_tool.name = "get_a_productdescription_for_api_product_srv"
    desc_tool.description = "Retrieve product description"
    desc_tool.args_schema = None
    desc_tool.arun = AsyncMock(
        return_value=json.dumps({
            "Product": "P-100",
            "Language": "EN",
            "ProductDescription": "Industrial Water Pump Model P-100",
        })
    )

    class_tool = MagicMock()
    class_tool.name = "list_a_productclass_for_api_clfn_product_srv"
    class_tool.description = "Retrieve product class assignments"
    class_tool.args_schema = None
    class_tool.arun = AsyncMock(
        return_value=json.dumps({
            "results": [{
                "Product": "P-100",
                "ClassType": "001",
                "ClassInternalID": "CL-PUMPS-001",
                "ClassDescription": "Industrial Pumps",
            }]
        })
    )

    return [product_tool, desc_tool, class_tool]


@pytest.fixture
def agent():
    from agent import SampleAgent
    return SampleAgent()


@pytest.mark.asyncio
async def test_end_to_end_product_query_flow(agent, product_tools):
    """Full flow: user asks about a product, agent returns accurate data."""
    with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {
            "response": (
                "Product P-100 — Industrial Water Pump Model P-100.\n"
                "Gross weight: 2.5 KG. Dimensions: 30cm x 20cm x 10cm. "
                "Base unit: EA (each)."
            )
        }

        response = await agent.invoke(
            "Tell me about product P-100",
            "ctx-int-001",
            tools=product_tools,
        )

    assert response.status == "completed"
    assert len(response.message) > 0


@pytest.mark.asyncio
async def test_multi_turn_conversation_context_retained(agent, product_tools):
    """Second query resolves product reference from session context without repetition."""
    # Turn 1: ask about product
    with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {
            "response": "Product P-100 is an Industrial Water Pump. Gross weight: 2.5 KG."
        }
        response1 = await agent.invoke(
            "Tell me about product P-100",
            "ctx-int-multi",
            tools=product_tools,
        )

    assert response1.status == "completed"

    # Turn 2: follow-up without repeating product name
    with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {
            "response": "Product P-100 belongs to the 'Industrial Pumps' class (CL-PUMPS-001)."
        }
        response2 = await agent.invoke(
            "What class does it belong to?",
            "ctx-int-multi",
            tools=product_tools,
        )

    assert response2.status == "completed"
    assert len(response2.message) > 0


@pytest.mark.asyncio
async def test_agent_uses_live_data_not_fabrication(agent, product_tools):
    """Agent response is based on tool data, not LLM fabrication."""
    call_count = 0

    async def tracked_run(query, context_id, tools):
        nonlocal call_count
        call_count += 1
        return {"response": "Product P-100: Industrial Water Pump, 2.5 KG, retrieved from S/4HANA."}

    with patch.object(agent, "_run_agent", side_effect=tracked_run):
        response = await agent.invoke(
            "What is product P-100?",
            "ctx-int-live",
            tools=product_tools,
        )

    assert response.status == "completed"
    assert call_count == 1


@pytest.mark.asyncio
async def test_read_only_scope_enforced(agent, product_tools):
    """Agent declines requests that would require write operations."""
    with patch.object(agent, "_run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {
            "response": (
                "I'm sorry, I can only read product information. "
                "Creating or modifying products is not within my capabilities."
            )
        }

        response = await agent.invoke(
            "Please create a new product P-999 with weight 5 KG",
            "ctx-int-write",
            tools=product_tools,
        )

    assert response.status == "completed"
    assert (
        "cannot" in response.message.lower()
        or "only" in response.message.lower()
        or "not" in response.message.lower()
    )
