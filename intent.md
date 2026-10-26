# Product Master Data AI Agent for Sales Representatives

SAP S/4HANA Public Cloud AI Agent — natural language product data queries via Joule

## Business challenge

Sales Representatives spend significant time manually searching for product master data and pricing information in SAP S/4HANA. With 50 reps querying product information multiple times a day, this creates a bottleneck that slows down customer conversations and reduces responsiveness. The goal is to enable reps to ask natural language questions about product details (descriptions, categories, weights, dimensions, etc.) as well as standard list prices and customer-specific pricing conditions — and receive instant, accurate answers directly within Joule.

## Business Goals & Success Criteria

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Time to find product information | 5 minutes | Under 30 seconds | — | Product Master Data Query (Lead to Cash) | user |

## Key Milestones

1. **Query Understanding** — Agent correctly interprets a natural language product question from a Sales Rep
2. **Data Retrieval** — Agent retrieves accurate product master data from S/4HANA Public Cloud via API
3. **Answer Delivery** — Agent returns a clear, structured answer to the Sales Rep within Joule
4. **Multi-turn Conversations** — Agent handles follow-up questions within the same session
5. **Go-Live** — Agent is deployed and accessible via Joule for all 50 Sales Representatives

## Business Architecture (RBA)

### End-to-End Process

Lead to Cash Standard B2B

### Process Hierarchy

```
Lead to Cash Standard B2B (E2E)
└── Plan to Optimize Marketing and Sales
    └── Plan prices and promotions (BPS-359_002)
        └── Plan and define sales prices
```

### Summary

Sales Representatives querying product master data maps to the Lead to Cash (Standard B2B) E2E process, specifically the Plan prices and promotions sub-process, where product details and pricing definitions are central to enabling effective customer engagement.

## Fit Gap Analysis

| Requirement (business) | Standard asset(s) found | API ORD ID | MCP Server ORD ID | MCP Server Version | Webhook API ORD ID | Data Product ORD ID | Gap? | Notes / assumptions |
| ---------------------- | ----------------------- | ---------- | ----------------- | ------------------ | ------------------ | ------------------- | ---- | ------------------- |
| Query product details (description, category, dimensions, weight) | SAP S/4HANA Cloud Public Edition — Sales Price Planning and Definition | `sap.s4:apiResource:API_PRODUCT_SRV:v1` | — | — | — | — | Yes | No pre-built MCP server; custom MCP translation file required |
| Query product classification & technical attributes | SAP S/4HANA Cloud Public Edition | `sap.s4:apiResource:API_CLFN_PRODUCT_SRV:v1` | — | — | — | — | Yes | No pre-built MCP server; custom MCP translation file required |
| Query standard list prices per product | SAP S/4HANA Cloud Public Edition | `sap.s4:apiResource:SALESPRICE_0001:v1` | — | — | — | — | Yes | No pre-built MCP server; custom MCP translation file required |
| Query customer-specific pricing conditions & discounts | SAP S/4HANA Cloud Public Edition | `sap.s4:apiResource:API_SLSPRICINGCONDITIONRECORD_SRV:v1` | — | — | — | — | Yes | No pre-built MCP server; custom MCP translation file required |
| Natural language interface for Sales Reps | AI Agent with Joule integration | — | — | — | — | — | Yes | Requires Python A2A agent; no standard SAP product covers this |

### Key findings

- Four S/4HANA Public Cloud APIs are now in-scope: Product Master (API_PRODUCT_SRV), Product Classification (API_CLFN_PRODUCT_SRV), Sales Price - Retrieve (SALESPRICE_0001), and Condition Record for Pricing in Sales (API_SLSPRICINGCONDITIONRECORD_SRV).
- Availability APIs and SOAP-based pricing services (e.g., Manage Sales Price Lists, Query Price Lists) are marked unavailable in this landscape and are excluded from scope.
- No pre-built MCP servers exist for any of these APIs; custom MCP translation files must be generated for all four.
- The natural language interface and reasoning layer requires a custom Python AI agent (A2A protocol).
- Integration into Joule is the target channel, aligning with SAP's embedded AI strategy.
- Scope covers product details and pricing (standard list prices + customer-specific conditions), per user confirmation.

## Recommendations

### AI-Powered Product Data Agent for Joule

#### Executive Summary

Python A2A agent in Joule answering product queries via S/4HANA APIs

#### Recommended Solution

Build a pro-code Python AI agent (A2A protocol) that integrates with SAP S/4HANA Public Cloud via custom MCP tools generated from the Product Master and Product Classification OData APIs. The agent is embedded into Joule, allowing Sales Representatives to ask natural language questions and receive instant, structured answers about product details without navigating the S/4HANA UI.

#### Recommended solution category

AI Agent

#### Intent fit
90%
