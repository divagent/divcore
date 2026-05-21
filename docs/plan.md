Phase 0: Lock Current Behavior

Add a baseline health check

Add/confirm /health.
Test: app starts and /health returns OK.
Fix local test stability

Mock Gemini in tests/test_agent_brain.py.
Test: uv run pytest passes without external API keys.
Document current env vars

Create .env.example.
Test: a new developer can see required keys without opening code.
Phase 1: Make Core Dividend Backend Solid

Fix DB session dependency

Change get_db to yield AsyncSession, not raw connection.
Test: /div_show/list and /div_rag_contract/rag/rebuild-chunks still work.
Confirm snapshot semantics

Add tests proving upsert_df_symbol_only keeps one current row per symbol.
Test: insert same symbol twice, latest row wins.
Validate dividend rows against symbol universe

During Nasdaq ingestion, accept only symbols in curated symbols.
Test: known symbol imports; unknown symbol is skipped with count.
Add ingestion result details

Return inserted_or_updated, skipped_not_in_universe, source, date_range.
Test: endpoint response includes counts.
Phase 2: Source Providers As Clean Services

Create provider interface

Example: DividendProvider.fetch_dividends(date_from, date_to).
Implement current Nasdaq provider behind that interface.
Test: Nasdaq provider returns normalized rows.
Add Alpha Vantage provider

Use free DIVIDENDS endpoint per symbol.
Test: with mocked HTTP, normalized rows match schema.
Add source provenance

Store/return source, source_updated_at, confirmed if available.
Test: provider rows carry provenance.
Add reconciliation service
Compare Nasdaq vs Alpha Vantage for same symbol/date.
Test: exact match, missing secondary, conflicting amount/date.
Phase 3: MCP Domain

Create div_mcp skeleton
Separate folder/repo or package.
Start with one tool: get_freshness_report.
Test: MCP server starts and tool returns static/real data.
Expose core read tools
get_universe_symbols
get_dividend_snapshot
get_dividend_by_symbol
Test each tool with known DB fixtures.
Expose ingestion tools
refresh_nasdaq_calendar
refresh_alpha_vantage_dividends
Test with mocked providers first.
Expose reconciliation tool
reconcile_dividend_sources
Test: returns match/conflict/missing classification.
Phase 4: RAG Domain

Make RAG service deterministic
Separate chunk build, embed, index, query functions.
Test: chunk text generated from a fixture dividend row.
Expose RAG through MCP
Tool: search_dividend_rag.
Test: mocked vector search returns expected source chunks.
Add changed-row indexing
Add needs_reindex, embedded_at, indexed_at.
Test: only changed rows are re-embedded.
Phase 5: Agent Domain

Create agent with MCP-only tools
Agent cannot import DB/provider code.
It can only call MCP.
Test: “What dividends are next week?” calls structured dividend tool.
Add routing decisions
Structured query -> dividend snapshot MCP.
Fuzzy explanation -> RAG MCP.
Conflict/stale data -> freshness/reconciliation MCP.
Test: mocked MCP calls verify correct route.
Add final answer schema
answer, data, sources, freshness, warnings.
Test: output validates with Pydantic.
Phase 6: Cron And Operations

Fix cron endpoint mismatch
Either update div_cron to /div_inject/div_daily or add alias route.
Test: GitHub Action curl receives success.
Make cron wait for job acceptance
Endpoint returns job id.
Cron logs job id.
Test: manual workflow shows job id.
Add job status table
Track started, completed, failed, counts.
Test: failed provider call records failed job.
Add freshness dashboard endpoint/tool
Latest symbol universe refresh.
Latest dividend refresh.
Latest RAG index time.
Test: MCP get_freshness_report returns all timestamps.
My suggested first sprint

Do these first, in order:

Fix tests so they do not require Gemini.
Fix DB session dependency.
Add snapshot upsert tests.
Add universe membership validation.
Add provider interface around current Nasdaq code.
Add Alpha Vantage provider with mocked tests.
Create first MCP tool: get_dividend_snapshot.