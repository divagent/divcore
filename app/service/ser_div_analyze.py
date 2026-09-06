"""Agent analysis for a single dividend calendar event.

Given a clicked calendar row, produce a grounded read on that dividend — NOT a
generic narrative. The agent works in two layers:

  1. FACT — has the board already declared this dividend? If a declared amount is
     on record (via a data provider or the news), that is the truth; if the
     calendar row disagrees, the row is stale and we say so.
  2. LEAD — for anything not yet declared, weigh the pressure that precedes a
     declaration: payout coverage, free cash flow, yield, analyst warnings, and
     retail/forum chatter — and call whether the payment is at risk BEFORE the
     company confirms it. That early read is the whole point of the app.

Everything is grounded in supplied quantitative facts + retrieved signals; the
model is told never to invent. Never raises — failures degrade to a low-signal
read so the panel always shows something.
"""

import asyncio
import json
from datetime import date, datetime, timezone

from app.agent.age_grounding import build_grounding
from app.agent.age_signals import gather_dividend_signals
from app.core.ai_logging import log_event
from app.adapters.gemini_chat import chat_completion_agent, deployment as _MODEL_NAME
from app.schemas.sch_analyze import AnalysisSource, AnalyzeRequest, AnalyzeResponse
from app.service.ser_div_reconcile import reconcile_declared


ANALYSIS_SYSTEM_PROMPT = (
    "You are a skeptical dividend-risk analyst. You are given ONE dividend calendar "
    "event (which may be STALE), verified quantitative FACTS (price, yield, amount "
    "trend), and multi-source SIGNALS (declared filings, fundamentals, analyst news, "
    "and retail forum chatter). Produce a grounded read.\n\n"
    "Work in two layers:\n"
    "1) FACT CHECK: If the SIGNALS show the board has DECLARED a dividend for this "
    "ex-date, that amount and date are the truth. If the calendar row's amount "
    "disagrees with the declared amount, state clearly that the row is stale and "
    "give the real number.\n"
    "2) LEADING READ: If it is NOT yet declared, judge whether the payment is likely "
    "to be maintained, cut, or raised — using payout coverage, free cash flow, the "
    "yield, analyst commentary, and forum sentiment. A very high yield, payout ratio "
    "over ~100%, negative/declining cash flow, or credible cut chatter are RED FLAGS. "
    "Do NOT default to 'stable growth' — say what the evidence actually shows.\n\n"
    "Respond ONLY with a single JSON object, no prose, matching exactly:\n"
    "{\n"
    '  "headline": string,   // one sentence; lead with the real number / the risk\n'
    '  "riskLabel": "low"|"medium"|"high",  // reliability of THIS payment as shown\n'
    '  "reasoning": string,  // 3-6 sentences citing the FACTS and SIGNALS: declared\n'
    "                        // status, coverage/payout, yield, and any cut/raise chatter\n"
    '  "sources": [ { "title": string, "url": string } ]  // ONLY urls from SIGNALS\n'
    "}\n"
    "Rules: Prefer declared facts over the calendar row. Never refuse. Never invent "
    "numbers or sources; only cite URLs present in the SIGNALS block. If evidence is "
    "thin, say so and lower confidence rather than guessing a rosy story."
)

_RISK = {"low", "medium", "high"}


def _kind_note(kind: str) -> str:
    return {
        "fact": "The row claims this ex-date/amount is CONFIRMED — verify against declared filings.",
        "estimate": "The row is a mechanical PATTERN ESTIMATE (not announced) — treat the amount as unverified.",
        "prediction": "The row is a forward-looking RESEARCH PREDICTION.",
    }.get(kind, "")


async def analyze_dividend(
    req: AnalyzeRequest, *, trace_id: str = "internal"
) -> AnalyzeResponse:
    symbol = (req.symbol or "").strip().upper()
    generated_at = datetime.now(timezone.utc).isoformat()
    facts = req.facts
    company = facts.companyName if facts else None
    log_event("analyze_dividend_start", trace_id=trace_id, symbol=symbol, kind=req.kind)

    amount_text = f"{req.amount:.4f}".rstrip("0").rstrip(".") if req.amount is not None else "TBD"
    conf_text = f"{round(req.confidence * 100)}%" if req.confidence is not None else "n/a"

    # Quantitative grounding from the browser's Yahoo facts (yield + amount trend).
    grounding = None
    if facts:
        grounding = build_grounding(
            price=facts.price,
            currency=facts.currency,
            dividends=[(d.exDate, d.amount) for d in facts.pastYearDividends],
            ttm_amount=facts.ttmAmount,
            forward_yield_pct=facts.forwardYield,
            trailing_yield_pct=facts.trailingYield,
            forward_rate=facts.forwardRate,
        )

    try:
        signals = await gather_dividend_signals(
            symbol, company_name=company, target_ex=req.exDate, trace_id=trace_id
        )

        # A declaration invalidates any forward-looking calendar row. Fire the
        # silent correction NOW so it runs concurrently with the analysis LLM
        # call below; we await it just before returning. Best-effort — it never
        # raises, so it can't break the panel.
        reconcile_task = (
            asyncio.create_task(
                reconcile_declared(
                    symbol,
                    signals.declared,
                    note=signals.declared_note,
                    fallback_ex_date=req.exDate,
                    trace_id=trace_id,
                )
            )
            if signals.declared
            else None
        )

        grounding_text = grounding.text if grounding else "(no quantitative facts supplied)"
        risk_hint = grounding.risk_hint if grounding else ""
        declared_line = ""
        if signals.declared:
            dd = signals.declared
            note = f" ({signals.declared_note})" if signals.declared_note else ""
            declared_line = (
                f"\nDECLARED / ANNOUNCED dividend on record: {dd.get('amount')} per share, "
                f"ex-date {dd.get('exDate')} (declared {dd.get('declarationDate') or 'n/a'}, "
                f"pays {dd.get('payDate') or 'n/a'}){note}. This is FACT — it OVERRIDES the "
                f"calendar row's amount ({amount_text}) if they differ. Lead your headline "
                "with the real declared number and say the row is stale."
            )

        user_content = (
            f"Today is {date.today().isoformat()}.\n\n"
            f"=== CALENDAR EVENT (may be STALE) ===\n"
            f"Company: {company or symbol} ({symbol})\n"
            f"Ex-date shown: {req.exDate or 'unknown'}\n"
            f"Amount shown: {amount_text}\n"
            f"Row type: {req.kind} — {_kind_note(req.kind)}\n"
            f"Model confidence (prediction rows only): {conf_text}\n"
            f"Row summary: {req.summary or '(none)'}\n\n"
            f"=== VERIFIED FACTS (price, yield, trend) ===\n{grounding_text}\n"
            f"{('Automated risk hint: ' + risk_hint) if risk_hint else ''}"
            f"{declared_line}\n\n"
            f"=== SIGNALS (declared filings, fundamentals, news, forums) ===\n{signals.text}"
        )

        raw = await chat_completion_agent(
            messages=[
                {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ]
        )
        data = json.loads(raw)

        risk = str(data.get("riskLabel", "")).lower()
        sources = [
            AnalysisSource(title=str(s.get("title", "")), url=str(s["url"]))
            for s in (data.get("sources") or [])
            if isinstance(s, dict) and s.get("url")
        ]
        # Fall back to the gathered sources if the model cited none.
        if not sources and signals.sources:
            sources = [
                AnalysisSource(title=s.get("title", ""), url=s["url"])
                for s in signals.sources[:4]
                if s.get("url")
            ]

        corrected = False
        if reconcile_task is not None:
            outcome = await reconcile_task  # already best-effort; never raises
            corrected = bool(outcome and outcome.get("corrected"))

        response = AnalyzeResponse(
            symbol=symbol,
            exDate=req.exDate,
            headline=str(data.get("headline", "") or ""),
            reasoning=str(data.get("reasoning", "") or ""),
            riskLabel=risk if risk in _RISK else "unknown",
            sources=sources,
            model=_MODEL_NAME,
            generatedAt=generated_at,
            corrected=corrected,
        )
    except Exception as exc:  # never surface an error box — degrade gracefully
        log_event(
            "analyze_dividend_failure",
            trace_id=trace_id,
            symbol=symbol,
            severity="HIGH",
            error=str(exc),
        )
        response = AnalyzeResponse(
            symbol=symbol,
            exDate=req.exDate,
            headline=f"Could not complete live analysis for {symbol}.",
            reasoning=(
                "The agent could not gather signals or parse a structured read for "
                "this event just now. Try again in a moment."
            ),
            riskLabel="unknown",
            sources=[],
            model=_MODEL_NAME,
            generatedAt=generated_at,
        )

    log_event(
        "analyze_dividend_done",
        trace_id=trace_id,
        symbol=symbol,
        risk=response.riskLabel,
    )
    return response
