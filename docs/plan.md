# Dividend Platform Roadmap

## Phase 0 — Lock Current Behavior

### 1. Add baseline health check
- Add or confirm `GET /health`
- Response: `200 OK`

**Test**
- App starts successfully
- `/health` returns `OK`

---

### 2. Fix local test stability
- Mock Gemini in `tests/test_agent_brain.py`
- Remove dependency on external API keys during test execution

**Test**
```bash
uv run pytest
```

Expected:
- All tests pass without external credentials

---

### 3. Document current environment variables
- Create `.env.example`
- Include all required keys and descriptions

**Test**
- New developer can identify required environment variables without reading code

---

# Phase 1 — Make Core Dividend Backend Solid

## 1. Fix DB session dependency
- Change `get_db()` to yield `AsyncSession`
- Remove raw connection usage

**Test**
- `/div_show/list` works
- `/div_rag_contract/rag/rebuild-chunks` works

---

## 2. Confirm snapshot semantics
- Add tests for `upsert_df_symbol_only`

Expected behavior:
- Only one current row per symbol
- Latest insert wins

**Test**
```text
Insert same symbol twice
→ latest row remains active
```

---

## 3. Validate dividend rows against symbol universe
During Nasdaq ingestion:
- Accept only symbols in curated universe
- Skip unknown symbols

**Test**
```text
Known symbol → imported
Unknown symbol → skipped + counted
```

---

## 4. Add ingestion result details

Return:

```json
{
  "inserted_or_updated": 0,
  "skipped_not_in_universe": 0,
  "source": "nasdaq",
  "date_range": {}
}
```

**Test**
- Endpoint response includes all counters

---

# Phase 2 — Source Providers as Clean Services

## 1. Create provider interface

Example:

```python
class DividendProvider:
    async def fetch_dividends(date_from, date_to):
        ...
```

Implement:
- Current Nasdaq provider behind interface

**Test**
- Nasdaq provider returns normalized dividend rows

---

## 2. Add Alpha Vantage provider

Use:
- Free `DIVIDENDS` endpoint
- Per-symbol ingestion

**Test**
- Mock HTTP responses
- Output matches normalized schema

---

## 3. Add source provenance

Store and expose:

```text
source
source_updated_at
confirmed
```

**Test**
- Provider rows preserve provenance fields

---

## 4. Add reconciliation service

Compare:
- Nasdaq
- Alpha Vantage

Classification:
- Match
- Missing secondary
- Conflict

**Test**
```text
same symbol + date
→ expected classification
```

---

# Phase 3 — MCP Domain

## 1. Create `div_mcp` skeleton

Structure:
- Separate folder/repo/package

Start tool:

```text
get_freshness_report
```

**Test**
- MCP server starts
- Tool returns data

---

## 2. Expose core read tools

Tools:

```text
get_universe_symbols
get_dividend_snapshot
get_dividend_by_symbol
```

**Test**
- Fixture-based verification

---

## 3. Expose ingestion tools

Tools:

```text
refresh_nasdaq_calendar
refresh_alpha_vantage_dividends
```

**Test**
- Mock providers

---

## 4. Expose reconciliation tool

Tool:

```text
reconcile_dividend_sources
```

Returns:

```text
match
conflict
missing
```

**Test**
- Expected classifications returned

---

# Phase 4 — RAG Domain

## 1. Make RAG service deterministic

Separate:

```text
chunk_build()
embed()
index()
query()
```

**Test**
- Chunk generation from fixture dividend row

---

## 2. Expose RAG through MCP

Tool:

```text
search_dividend_rag
```

**Test**
- Mock vector search
- Correct chunks returned

---

## 3. Add changed-row indexing

Fields:

```text
needs_reindex
embedded_at
indexed_at
```

**Test**
- Only changed rows re-embedded

---

# Phase 5 — Agent Domain

## 1. Create agent with MCP-only tools

Rules:
- Agent cannot import DB code
- Agent cannot import providers
- Agent communicates only through MCP

**Test**

Prompt:
```text
"What dividends are next week?"
```

Expected:
- Structured dividend MCP tool invoked

---

## 2. Add routing decisions

Routing:

| Query Type | Route |
|---|---|
| Structured | Dividend Snapshot MCP |
| Fuzzy explanation | RAG MCP |
| Conflict / stale | Freshness + Reconciliation MCP |

**Test**
- Mock MCP calls
- Correct routing verified

---

## 3. Add final answer schema

Schema:

```python
class AgentAnswer(BaseModel):
    answer: str
    data: dict
    sources: list
    freshness: dict
    warnings: list
```

**Test**
- Output validates via Pydantic

---

# Phase 6 — Cron and Operations

## 1. Fix cron endpoint mismatch

Choose one:

- Update `div_cron → /div_inject/div_daily`
- OR add alias route

**Test**
```bash
curl ...
```

Expected:
- Success response

---

## 2. Make cron wait for job acceptance

Endpoint returns:

```json
{
  "job_id": "..."
}
```

Cron:
- Logs job ID

**Test**
- Manual workflow shows accepted job

---

## 3. Add job status table

Track:

```text
started
completed
failed
counts
```

**Test**
- Failed provider calls recorded

---

## 4. Add freshness dashboard endpoint/tool

Expose:

```text
latest_symbol_universe_refresh
latest_dividend_refresh
latest_rag_index_time
```

**Test**
- `get_freshness_report` returns timestamps

---

# Suggested First Sprint

Do these in order:

1. Fix tests so they do not require Gemini
2. Fix DB session dependency
3. Add snapshot upsert tests
4. Add universe membership validation
5. Add provider interface around current Nasdaq code
6. Add Alpha Vantage provider with mocked tests
7. Create first MCP tool: `get_dividend_snapshot`