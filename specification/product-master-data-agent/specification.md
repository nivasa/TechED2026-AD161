# Specification: product-master-data-agent

> **Guidelines**: Read all applicable guidelines before executing ANY tasks below:
> - [guidelines.md](../guidelines.md) — Universal execution rules
> - [guidelines-agent.md](../guidelines-agent.md) — Universal agent patterns
> - [guidelines-agent-python.md](../guidelines-agent-python.md) — Python implementation details
> - [guidelines-agent-skills.md](../guidelines-agent-skills.md) — Runtime skills patterns
> - [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) — MCP integration patterns

---

## Basic Setup

- [x] Read the project input (`product-requirements-document.md`, `intent.md`)
- [x] Bootstrap agent code in `assets/product-master-data-agent/` using instructions from the `sap-agent-bootstrap` skill
- [x] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`

---

## Project-Specific Tasks

### Agent Identity & System Prompt

- [x] Set the agent name to `Product Master Data Agent` and description to `Answers natural language questions about SAP S/4HANA product master data for Sales Representatives`
- [x] Write a system prompt in `app/agent.py` with all required rules (read-only, context retention, product scope only, pagination limits, error relay)

### Natural Language Product Query (REQ-001)

- [x] Implement ability to answer natural language questions about a product via Product Master MCP tool
- [x] Agent extracts product identifier from natural language input
- [x] Agent returns structured, readable answer with product fields
- [x] Agent responds within Joule context

### Product Classification & Technical Attributes (REQ-002)

- [x] Implement ability to answer questions about product classification via Product Classification MCP tool
- [x] Agent returns class assignments and characteristic values
- [x] Agent clearly communicates missing classification data

### Multi-Turn Conversation (REQ-003)

- [x] Agent retains context across turns within the same session
- [x] Follow-up questions resolve product references from session context

### Standard List Prices (REQ-006)

- [x] Implement ability to answer questions about a product's standard list price via Sales Price MCP tool
- [x] Agent extracts product identifier and optionally sales organisation from natural language input
- [x] Agent returns price value, currency, and validity period in a clear, readable format
- [x] Agent returns "no price found" message when no record exists for the product

### Customer-Specific Pricing Conditions & Discounts (REQ-007)

- [x] Implement ability to answer questions about customer-specific pricing conditions via Pricing Conditions MCP tool
- [x] Agent extracts product and customer identifiers from natural language input
- [x] Agent returns applicable condition records (condition type, amount, currency, validity) in a readable format
- [x] Agent clearly communicates when no condition records are found for the given combination

### Data Accuracy & Source Transparency (REQ-005)

- [x] All product data returned from live S/4HANA API calls
- [x] API failures return clear error messages, no fabricated content

---

## API Integration

### MCP API Details

**MCP API:** `sap.s4:apiResource:API_PRODUCT_SRV:v1`
**MCP tool scope:** read-only
**Resources in scope:** `A_Product, A_ProductDescription, A_ProductPlant, A_ProductSalesDelivery, A_ProductBasicText`

**MCP API:** `sap.s4:apiResource:API_CLFN_PRODUCT_SRV:v1`
**MCP tool scope:** read-only
**Resources in scope:** `A_ClfnProduct, A_ClfnProductClass, A_ClfnProductCharc`

**MCP API:** `sap.s4:apiResource:SALESPRICE_0001:v1`
**MCP tool scope:** read-only
**Resources in scope:** `SalesPrice, SalesPriceValidity`

**MCP API:** `sap.s4:apiResource:API_SLSPRICINGCONDITIONRECORD_SRV:v1`
**MCP tool scope:** read-only
**Resources in scope:** `A_SlsPrcgCndnRecdValidity, A_SlsPrcgCndnRecdSuplmnt`

### API Spec Files

- `specification/product-master-data-agent/api-specs/API_PRODUCT_SRV.edmx` — Product Master (A2X), OData v2
- `specification/product-master-data-agent/api-specs/API_CLFN_PRODUCT_SRV.edmx` — Product Master Data Including Classification, OData v2
- `specification/product-master-data-agent/api-specs/SALESPRICE_0001.edmx` — Sales Price - Retrieve (A2X), OData v2
- `specification/product-master-data-agent/api-specs/API_SLSPRICINGCONDITIONRECORD_SRV.edmx` — Condition Record for Pricing in Sales, OData v2

---

## MCP Tool Integration

- [x] Invoke `mcp-translation-file` skill for `API_PRODUCT_SRV.edmx` → `specification/product-master-data-agent/mcps/API_PRODUCT_SRV/` (23 tools kept from 251)
- [x] Invoke `mcp-translation-file` skill for `API_CLFN_PRODUCT_SRV.edmx` → `specification/product-master-data-agent/mcps/API_CLFN_PRODUCT_SRV/` (20 tools kept from 72)
- [x] Invoke `mcp-translation-file` skill for `SALESPRICE_0001.edmx` → `specification/product-master-data-agent/mcps/SALESPRICE_0001/` (read-only, SalesPrice + SalesPriceValidity)
- [x] Invoke `mcp-translation-file` skill for `API_SLSPRICINGCONDITIONRECORD_SRV.edmx` → `specification/product-master-data-agent/mcps/API_SLSPRICINGCONDITIONRECORD_SRV/` (read-only, condition record entities)
- [x] Invoke `setup-solution` skill to register both MCP server assets and produce their `asset.yaml` files
- [x] Register 2 new MCP server assets (SALESPRICE_0001, API_SLSPRICINGCONDITIONRECORD_SRV) in `solution.yaml` and create their `asset.yaml` files via `setup-solution`
- [x] Read generated `asset.yaml` files and extract exact `ordId` values for agent `requires`
- [x] Add 2 new MCP server `ordId` values to agent `asset.yaml` under `requires`
- [x] Wire MCP tool loading in `app/agent.py` using `get_mcp_tools()` from `mcp_tools` module
- [x] Add both MCP server dependencies to agent `asset.yaml` under `requires`
- [x] Update agent system prompt in `app/agent.py` to include pricing capabilities (standard prices, customer conditions)
- [x] Update `mcp-mock.json` to include mock tool responses for the 2 new pricing MCP servers

---

## Business Instrumentation

- [x] M1 — Query Understanding: `M1.achieved/missed` log + OTel span
- [x] M2 — Data Retrieval: `M2.achieved/missed` log + OTel span
- [x] M3 — Answer Delivery: `M3.achieved/missed` log + OTel span
- [x] M4 — Multi-Turn Conversation: `M4.achieved/missed` log + OTel span
- [x] M5 — Go-Live: `M5.achieved/missed` log — update to include pricing availability confirmation
- [x] `_run_agent()` helper extracts business logic from `stream()` (no OTel inside async generator)
- [x] `bootstrap(app)` called after `app = server.build()` in `main.py`

---

## Testing

- [x] `conftest.py` sets `IBD_TESTING=true`
- [x] `tests/test_product_query.py` — product master data query flow (6 tests)
- [x] `tests/test_classification_query.py` — product classification query flow (4 tests)
- [x] `tests/test_error_handling.py` — API failure and edge case handling (4 tests)
- [x] `tests/test_not_found.py` — product not found response (3 tests)
- [x] `tests/test_integration.py` — end-to-end multi-turn conversation flow (4 tests)
- [x] `tests/test_pricing_query.py` — standard list price query flow (4 tests)
- [x] `tests/test_pricing_conditions.py` — customer-specific pricing conditions query flow (4 tests)
- [x] Run `pytest` from `assets/product-master-data-agent/` — verify all tests pass including new pricing tests
- [x] `test_report.json` exists in `assets/product-master-data-agent/`
