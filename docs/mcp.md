# Recommended Build Order: MCP Before Agent

Reason: MCP should become the stable tool boundary.

Agents become easier afterward because they only need to call tools; they should not know DB tables, provider code, ingestion code, or RAG internals.

## 1. Keep Core Backend As-Is

This repo remains the deterministic dividend backend.

Responsibilities:

- DB
- ingestion
- providers
- RAG services
- FastAPI admin endpoints
- FastAPI read endpoints

---

## 2. Extract / Build MCP Domain Next

Create `div_mcp` as its own package / repo / domain.

Expose stable tools:

- `get_dividend_snapshot`
- `get_dividend_by_symbol`
- `get_universe_symbols`
- `refresh_nasdaq_calendar`
- `refresh_alpha_vantage_dividends`
- `search_dividend_rag`

Future tools:

- `get_freshness_report`
- `reconcile_dividend_sources`

Implementation approach:

- MCP calls backend through HTTP initially.
- Avoid importing DB or service modules across repositories.
- Preserve clear boundaries.

---

## 3. Build Agent Domain After MCP

Agent repo should only know:

- MCP client
- routing logic
- answer schema
- prompt / decision policy

Agent should **not** import:

- `app.db`
- `app.service`
- `app.providers`

---

## Dependency Direction

```text
Agent repo
   ↓ calls
MCP repo/domain
   ↓ calls
Core backend FastAPI
   ↓ uses
DB/providers/RAG
```

---

## Why Not Agent First?

If you build the agent first:

- backend internals leak into agent logic
- contracts become unstable
- later refactoring becomes expensive

If you build MCP first:

- agent starts with a stable interface
- backend remains replaceable
- tool contracts become reusable across clients

---

## First Concrete Step

Create MCP tool contracts around existing backend HTTP endpoints.

Start with read-only tools:

- `get_dividend_snapshot`
- `get_dividend_by_symbol`
- `get_universe_symbols`

Then add:

1. ingestion tools
2. RAG tools
3. agent layer