"""Agent analysis for a single dividend calendar event.

Given a clicked calendar row (symbol + ex-date + amount + kind), pull recent
live news and ask Gemini for a structured read: a one-line headline, a coarse
reliability label, and a few sentences of reasoning covering payment history,
cadence stability, coverage, and the confidence behind this ex-date.

Never raises — on any failure it returns a low-signal response with the reason
in `reasoning`, so the panel always shows something rather than an error box.
"""

import json
from datetime import date, datetime, timezone

from app.agent.age_tools import search_web_tool
from app.core.ai_logging import log_event
from app.llm.gemini_chat import chat_completion_agent, deployment as _MODEL_NAME
from app.schemas.sch_analyze import AnalysisSource, AnalyzeRequest, AnalyzeResponse


ANALYSIS_SYSTEM_PROMPT = (
    "You are an elite dividend analyst. You are given ONE upcoming dividend "
    "calendar event and live NEWS about the company. Explain what this event "
    "means and how much to trust it. Respond ONLY with a single JSON object, no "
    "prose, matching exactly this schema:\n"
    "{\n"
    '  "headline": string,      // one punchy sentence, the key takeaway\n'
    '  "riskLabel": "low"|"medium"|"high",  // reliability of THIS payment happening as shown\n'
    '  "reasoning": string,     // 3-5 sentences: payment history & cadence stability,\n'
    "                           // payout coverage/affordability, and why the ex-date/amount\n"
    "                           // is or isn't trustworthy. Reference the NEWS when relevant.\n"
    '  "sources": [ { "title": string, "url": string } ]  // ONLY urls present in NEWS\n'
    "}\n"
    "Rules: 'fact' rows are confirmed/announced — treat the date and amount as "
    "reliable and focus on cadence and coverage. 'estimate' rows are a mechanical "
    "projection from history — flag that they are not yet announced. 'prediction' "
    "rows are a forward-looking research guess — weigh the given confidence and any "
    "news of a cut/suspension. Never refuse. Never invent sources; only cite URLs "
    "that appear in the NEWS block."
)

_RISK = {"low", "medium", "high"}


def _kind_note(kind: str) -> str:
    return {
        "fact": "This ex-date and amount are CONFIRMED/announced.",
        "estimate": "This is a mechanical PATTERN ESTIMATE (not yet announced).",
        "prediction": "This is a forward-looking RESEARCH PREDICTION.",
    }.get(kind, "")


async def analyze_dividend(
    req: AnalyzeRequest, *, trace_id: str = "internal"
) -> AnalyzeResponse:
    symbol = (req.symbol or "").strip().upper()
    generated_at = datetime.now(timezone.utc).isoformat()
    log_event("analyze_dividend_start", trace_id=trace_id, symbol=symbol, kind=req.kind)

    amount_text = f"${req.amount:.2f}" if req.amount is not None else "amount TBD"
    conf_text = (
        f"{round(req.confidence * 100)}%" if req.confidence is not None else "n/a"
    )

    try:
        news = await search_web_tool(
            f"{symbol} dividend {req.exDate or ''} payout coverage announcement "
            f"cut suspension {date.today().year}"
        )
        news_text = news.get("data") or news.get("error") or "No recent news found."

        user_content = (
            f"Today is {date.today().isoformat()}.\n"
            f"=== DIVIDEND EVENT ===\n"
            f"Company: {symbol}\n"
            f"Ex-date: {req.exDate or 'unknown'}\n"
            f"Amount: {amount_text}\n"
            f"Type: {req.kind} — {_kind_note(req.kind)}\n"
            f"Model confidence (prediction rows only): {conf_text}\n"
            f"Calendar summary: {req.summary or '(none)'}\n\n"
            f"=== NEWS (live web) ===\n{news_text}"
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
        response = AnalyzeResponse(
            symbol=symbol,
            exDate=req.exDate,
            headline=str(data.get("headline", "") or ""),
            reasoning=str(data.get("reasoning", "") or ""),
            riskLabel=risk if risk in _RISK else "unknown",
            sources=sources,
            model=_MODEL_NAME,
            generatedAt=generated_at,
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
                "The agent could not fetch news or parse a structured read for this "
                "event just now. Try again in a moment."
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
