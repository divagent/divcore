"""Dividend-prediction routine.

A focused, deterministic pipeline (not the free-form ReAct loop) that:
  (a) pulls dividend history via the existing RAG tool,
  (b) pulls recent news / company announcements via the existing web-search tool,
  (c) asks Gemini for a structured JSON verdict, validated against
      `DividendPrediction`.

Per the locked product decision, a weak/unreliable pattern is NEVER dropped:
on low signal or parse failure we still return a prediction, marked LOW confidence,
with the uncertainty carried in `reasoning`.
"""

import json
from datetime import date, datetime, timezone

from app.agent.age_tools import search_web_tool
from app.agent.agent_schema import DividendPrediction
from app.llm.gemini_chat import chat_completion_agent, deployment as _MODEL_NAME
from app.core.ai_logging import log_event
from app.schemas.sch_predict import (
    FactsLayer,
    PatternLayer,
    PredictedNext,
    ResearchLayer,
    ResearchSource,
)


# ---------------------------------------------------------------------------
# Layer 3 — research prediction over authoritative facts + detected pattern.
# ---------------------------------------------------------------------------

RESEARCH_SYSTEM_PROMPT = (
    "You are an elite dividend-forecasting analyst. You are given a company's "
    "CONFIRMED dividend facts, a mechanically-detected PATTERN, and live NEWS. "
    "The facts and pattern are authoritative — do NOT contradict them. Your job "
    "is the forward-looking question the pattern cannot answer: will the company "
    "KEEP paying on this pattern? Respond ONLY with a single JSON object, no prose, "
    "matching exactly this schema:\n"
    "{\n"
    '  "willMaintainPattern": boolean,\n'
    '  "confidence": number,                 // 0.0-1.0\n'
    '  "predictedNext": {\n'
    '    "exDate": "YYYY-MM-DD"|null,         // default to the pattern\'s next projected date\n'
    '    "amount": number|null,\n'
    '    "direction": "up"|"down"|"constant"  // vs. the most recent confirmed dividend\n'
    "  },\n"
    '  "reasoning": string,                   // 1-3 sentences citing the evidence\n'
    '  "sources": [ { "title": string, "url": string } ]  // ONLY urls present in NEWS\n'
    "}\n"
    "Rules: if the company recently signaled a cut/suspension or the pattern is "
    "irregular, LOWER the confidence and say why. Never refuse. Never invent sources; "
    "only cite URLs that appear in the NEWS block."
)


def _facts_text(facts: FactsLayer) -> str:
    lines = [f"  {d.exDate}: {d.amount}" for d in facts.confirmed]
    out = "Confirmed past-year dividends (authoritative):\n" + ("\n".join(lines) or "  (none)")
    if facts.specials:
        out += "\nSpecials (excluded from cadence): " + ", ".join(
            f"{d.exDate}={d.amount}" for d in facts.specials
        )
    if facts.notes:
        out += "\nNotes: " + " | ".join(facts.notes)
    return out


def _pattern_text(pattern: PatternLayer) -> str:
    proj = ", ".join(f"{p.exDate}~${p.amount}" for p in pattern.projected) or "(none)"
    return (
        f"frequency={pattern.frequency}, paymentsPerYear={pattern.paymentsPerYear}, "
        f"typicalAmount={pattern.typicalAmount}, trend={pattern.amountTrend}, "
        f"regular={pattern.regular}\nSummary: {pattern.summary}\nProjected next: {proj}"
    )


async def research_prediction(
    symbol: str,
    facts: FactsLayer,
    pattern: PatternLayer,
    *,
    trace_id: str = "internal",
) -> ResearchLayer:
    """Layer 3: reason over the given facts + pattern (NOT re-derived) plus live
    web news, and return a structured, sourced forward-looking prediction. Never
    raises — on any failure returns a LOW-confidence layer that falls back to the
    pattern's next projected payment."""
    symbol = (symbol or "").strip().upper()
    today = date.today().isoformat()
    generated_at = datetime.now(timezone.utc).isoformat()

    # A sensible default that never contradicts the pattern.
    default_next = PredictedNext(
        exDate=pattern.projected[0].exDate if pattern.projected else None,
        amount=pattern.projected[0].amount if pattern.projected else pattern.typicalAmount,
        direction="up" if pattern.amountTrend == "increasing"
        else "down" if pattern.amountTrend == "decreasing"
        else "constant",
    )

    try:
        news = await search_web_tool(
            f"{symbol} dividend announcement next ex-dividend date and amount {date.today().year}"
        )
        news_text = news.get("data") or news.get("error") or "No recent news found."

        user_content = (
            f"Today is {today}. Company: {symbol}.\n\n"
            f"=== CONFIRMED FACTS ===\n{_facts_text(facts)}\n\n"
            f"=== DETECTED PATTERN ===\n{_pattern_text(pattern)}\n\n"
            f"=== NEWS (live web) ===\n{news_text}"
        )
        raw = await chat_completion_agent(
            messages=[
                {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ]
        )
        data = json.loads(raw)

        pn = data.get("predictedNext") or {}
        predicted_next = PredictedNext(
            exDate=pn.get("exDate") or default_next.exDate,
            amount=pn.get("amount") if pn.get("amount") is not None else default_next.amount,
            direction=pn.get("direction") or default_next.direction,
        )
        sources = [
            ResearchSource(title=str(s.get("title", "")), url=str(s["url"]))
            for s in (data.get("sources") or [])
            if isinstance(s, dict) and s.get("url")
        ]
        research = ResearchLayer(
            willMaintainPattern=bool(data.get("willMaintainPattern", True)),
            confidence=float(data.get("confidence", 0.0) or 0.0),
            predictedNext=predicted_next,
            reasoning=str(data.get("reasoning", "") or ""),
            sources=sources,
            model=_MODEL_NAME,
            generatedAt=generated_at,
        )
    except Exception as exc:  # never drop the layer — degrade to the pattern.
        log_event(
            "research_prediction_failure",
            trace_id=trace_id,
            symbol=symbol,
            severity="HIGH",
            error=str(exc),
        )
        research = ResearchLayer(
            willMaintainPattern=pattern.regular,
            confidence=0.0,
            predictedNext=default_next,
            reasoning=(
                "Could not complete web research; falling back to the detected "
                "pattern as a LOW-confidence prediction rather than dropping it."
            ),
            sources=[],
            model=_MODEL_NAME,
            generatedAt=generated_at,
        )

    log_event(
        "research_prediction_done",
        trace_id=trace_id,
        symbol=symbol,
        confidence=research.confidence,
        will_maintain=research.willMaintainPattern,
    )
    return research
