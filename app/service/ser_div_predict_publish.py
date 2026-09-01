"""Orchestrator: turn the frontend's authoritative facts into all three labeled
layers and (optionally) publish them to the public Google Calendar.

Contract: `src/data/ai-query.contract.md` (frontend repo). One call, three layers:

    layer 1  facts     — echoed verbatim from the request (NEVER re-derived here)
    layer 2  pattern    — age_pattern.build_facts_and_pattern (heuristics, no LLM)
    layer 3  research    — age_predictor.research_prediction (web + LLM, sourced)
    calendar             — one all-day event per (symbol, ex-date), upserted

`publishToCalendar=False` computes all three layers and writes nothing (preview).
Calendar writes are best-effort: a failure is captured in `calendar.errors` and
never aborts the response. The layer-3 prediction is also persisted (best-effort)
into `dividend_predictions` for continuity with the old flow.
"""

import asyncio
from datetime import date
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncConnection

from app.agent.age_pattern import build_facts_and_pattern
from app.agent.age_predictor import research_prediction
from app.agent.agent_schema import DividendPrediction
from app.core.ai_logging import log_event
from app.db.repo.repo_div_prediction import DivPredictionRepo
from app.schemas.sch_predict import (
    CalendarLayer,
    CalendarWrite,
    FactsLayer,
    PatternLayer,
    PredictRequest,
    PredictResponse,
    ResearchLayer,
)
from app.service.ser_div_reconcile import reconcile_declared
from app.service.ser_gcal_publish import CalendarNotConfigured, upsert_event

# Precedence when several layers land on the same ex-date: prediction wins, then
# estimate, then fact. (Past facts and future projections rarely collide, but the
# prediction and the first estimate often share a date.)
_KIND_RANK = {"fact": 0, "estimate": 1, "prediction": 2}

_ARROW = {"up": "↑", "down": "↓", "constant": "→"}


def _fmt_amount(amount: Optional[float]) -> str:
    return f"${amount:.2f}" if amount is not None else "amount TBD"


def _plan_events(
    symbol: str,
    facts: FactsLayer,
    pattern: PatternLayer,
    research: ResearchLayer,
) -> list[dict]:
    """Build the list of calendar items, one per ex-date (highest-rank kind wins)."""
    by_date: dict[str, dict] = {}

    def consider(ex_date: Optional[str], kind: str, item: dict) -> None:
        if not ex_date:
            return
        existing = by_date.get(ex_date)
        if existing is None or _KIND_RANK[kind] > _KIND_RANK[existing["kind"]]:
            by_date[ex_date] = {"exDate": ex_date, "kind": kind, **item}

    for d in facts.confirmed:
        consider(d.exDate, "fact", {
            "summary": f"{symbol} {_fmt_amount(d.amount)} (confirmed)",
            "description": f"Confirmed dividend for {symbol} on {d.exDate}.",
            "amount": d.amount,
            "confidence": None,
        })

    for p in pattern.projected:
        consider(p.exDate, "estimate", {
            "summary": f"{symbol} {_fmt_amount(p.amount)} (estimate)",
            "description": f"Pattern estimate for {symbol}. {pattern.summary}",
            "amount": p.amount,
            "confidence": None,
        })

    nxt = research.predictedNext
    if nxt.exDate:
        pct = round(research.confidence * 100)
        consider(nxt.exDate, "prediction", {
            "summary": f"{symbol} {_fmt_amount(nxt.amount)} "
                       f"({_ARROW.get(nxt.direction, '→')} prediction {pct}%)",
            "description": (
                f"Research prediction for {symbol}.\n"
                f"Will maintain pattern: {research.willMaintainPattern}\n"
                f"Confidence: {pct}%\n\n{research.reasoning}"
                + ("\n\nSources:\n" + "\n".join(f"  - {s.url}" for s in research.sources)
                   if research.sources else "")
            ),
            "amount": nxt.amount,
            "confidence": research.confidence,
        })

    return sorted(by_date.values(), key=lambda e: e["exDate"])


async def _publish_all(
    symbol: str, events: list[dict], *, trace_id: str
) -> CalendarLayer:
    written: list[CalendarWrite] = []
    errors: list[str] = []

    for ev in events:
        try:
            result = await asyncio.to_thread(
                upsert_event,
                symbol=symbol,
                ex_date=ev["exDate"],
                summary=ev["summary"],
                description=ev["description"],
                kind=ev["kind"],
                amount=ev.get("amount"),
                confidence=ev.get("confidence"),
                trace_id=trace_id,
            )
            written.append(CalendarWrite(
                exDate=ev["exDate"],
                kind=ev["kind"],
                googleEventId=result.get("id"),
                status=result.get("action", "created"),
            ))
        except CalendarNotConfigured as exc:
            # Report once and stop trying the rest — all writes would fail the same way.
            errors.append(str(exc))
            log_event(
                "predict_publish_calendar_unconfigured",
                trace_id=trace_id, symbol=symbol, severity="MEDIUM",
            )
            break
        except Exception as exc:  # keep going; one bad write shouldn't sink the rest
            errors.append(f"{ev['exDate']} ({ev['kind']}): {exc}")
            log_event(
                "predict_publish_calendar_failure",
                trace_id=trace_id, symbol=symbol, ex_date=ev["exDate"],
                severity="HIGH", error=str(exc),
            )

    return CalendarLayer(written=written, errors=errors)


async def _persist_prediction(
    db: AsyncConnection,
    symbol: str,
    research: ResearchLayer,
    calendar: CalendarLayer,
    *,
    trace_id: str,
) -> None:
    """Best-effort upsert of the layer-3 prediction into dividend_predictions."""
    nxt = research.predictedNext
    google_event_id = next(
        (w.googleEventId for w in calendar.written
         if w.kind == "prediction" and w.exDate == nxt.exDate),
        None,
    )
    prediction = DividendPrediction(
        symbol=symbol,
        predicted_amount=nxt.amount,
        predicted_ex_date=nxt.exDate,
        direction=nxt.direction,
        confidence=research.confidence,
        reasoning=research.reasoning,
        sources=[s.url for s in research.sources],
    )
    try:
        repo = DivPredictionRepo(db)
        await repo.upsert_prediction(prediction, google_event_id=google_event_id)
    except Exception as exc:  # persistence is not on the critical path
        log_event(
            "predict_persist_failure",
            trace_id=trace_id, symbol=symbol, severity="MEDIUM", error=str(exc),
        )


async def predict_and_publish(
    req: PredictRequest, db: AsyncConnection, *, trace_id: str = "internal"
) -> PredictResponse:
    """Compute all three layers from the request's authoritative facts, optionally
    publish, persist the prediction, and return the full labeled response."""
    symbol = req.symbol.strip().upper()
    as_of = req.asOf or date.today().isoformat()

    log_event("predict_publish_start", trace_id=trace_id, symbol=symbol,
              publish=req.publishToCalendar, n_facts=len(req.facts.pastYearDividends))

    # Layers 1 & 2 — from the frontend's facts, no re-derivation.
    facts, pattern = build_facts_and_pattern(req.facts.pastYearDividends)

    # Layer 3 — research over those authoritative facts + the detected pattern,
    # grounded in price/yield and multi-source signals (declared, coverage, news).
    research = await research_prediction(
        symbol,
        facts,
        pattern,
        trace_id=trace_id,
        price=req.facts.price,
        currency=req.currency,
        ttm_amount=req.facts.ttmAmount,
        company_name=req.facts.companyName,
    )

    # Calendar — one event per ex-date, upserted (or preview: write nothing).
    calendar = CalendarLayer()
    if req.publishToCalendar:
        events = _plan_events(symbol, facts, pattern, research)
        calendar = await _publish_all(symbol, events, trace_id=trace_id)

        # If the board has already declared, the row we just wrote is a fact, not a
        # prediction. Reconcile AFTER publishing so the declared 'fact' overwrites
        # the prediction on its true date and supersedes any stale-dated row.
        if research.declared:
            await reconcile_declared(
                symbol,
                research.declared.model_dump(),
                note=research.declared.note,
                trace_id=trace_id,
            )

    await _persist_prediction(db, symbol, research, calendar, trace_id=trace_id)

    log_event("predict_publish_done", trace_id=trace_id, symbol=symbol,
              written=len(calendar.written), errors=len(calendar.errors))

    return PredictResponse(
        symbol=symbol,
        asOf=as_of,
        currency=req.currency,
        facts=facts,
        pattern=pattern,
        research=research,
        calendar=calendar,
    )
