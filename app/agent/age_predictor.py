"""Dividend-prediction routine (layer 3).

Since the migration onto the Strands + divmcp pipeline, this module is a thin
CLIENT: it computes the deterministic quantitative grounding (price/yield/trend)
from the authoritative facts, then hands the facts + pattern + grounding to
divagent's research agent, which discovers the divmcp tools (`dividend_tracker`,
`web_search`, `fetch_url`) and runs the reason -> call-tool -> observe loop to
produce a structured, sourced forward-looking prediction.

Per the locked product decision, a weak/unreliable pattern is NEVER dropped: if
divagent is unreachable or errors we still return a prediction here, marked LOW
confidence, falling back to the pattern's next projected payment. This function
never raises.
"""

from datetime import date, datetime, timezone
from typing import Optional

import httpx

from app.agent.age_grounding import build_grounding
from app.config import get_settings_singleton
from app.core.ai_logging import log_event
from app.schemas.sch_predict import (
    FactsLayer,
    PatternLayer,
    PredictedNext,
    ResearchLayer,
)

# The agent loop makes several live web calls, so give it a generous read budget
# while keeping the connect timeout short.
_TIMEOUT = httpx.Timeout(10.0, read=120.0)


def _default_next(pattern: PatternLayer) -> PredictedNext:
    """A predictedNext that never contradicts the pattern (fallback floor)."""
    return PredictedNext(
        exDate=pattern.projected[0].exDate if pattern.projected else None,
        amount=pattern.projected[0].amount if pattern.projected else pattern.typicalAmount,
        direction="up" if pattern.amountTrend == "increasing"
        else "down" if pattern.amountTrend == "decreasing"
        else "constant",
    )


def _fallback(pattern: PatternLayer, model_label: str, generated_at: str) -> ResearchLayer:
    return ResearchLayer(
        willMaintainPattern=pattern.regular,
        confidence=0.0,
        predictedNext=_default_next(pattern),
        reasoning=(
            f"Could not complete agent research (model: {model_label}); falling back "
            "to the detected pattern as a LOW-confidence prediction rather than "
            "dropping it."
        ),
        sources=[],
        model=model_label,
        generatedAt=generated_at,
    )


async def research_prediction(
    ticker: str,
    facts: FactsLayer,
    pattern: PatternLayer,
    *,
    trace_id: str = "internal",
    price: Optional[float] = None,
    currency: Optional[str] = None,
    ttm_amount: Optional[float] = None,
    company_name: Optional[str] = None,
) -> ResearchLayer:
    """Layer 3: delegate the forward-looking research to divagent's Strands agent.

    Computes the quantitative grounding here (deterministic), forwards facts +
    pattern + grounding to divagent, and returns its structured `ResearchLayer`.
    Never raises — on any failure returns a LOW-confidence layer that falls back to
    the pattern's next projected payment."""
    ticker = (ticker or "").strip().upper()
    today = date.today().isoformat()
    generated_at = datetime.now(timezone.utc).isoformat()
    model_label = "unavailable"

    grounding = build_grounding(
        price=price,
        currency=currency,
        dividends=[(d.exDate, d.amount) for d in facts.confirmed],
        ttm_amount=ttm_amount,
    )

    settings = get_settings_singleton()
    url = f"{settings.DIVAGENT_URL.rstrip('/')}/api/v1/predict/research"
    payload = {
        "ticker": ticker,
        "companyName": company_name,
        "currency": currency,
        "today": today,
        "facts": facts.model_dump(),
        "pattern": pattern.model_dump(),
        "groundingText": grounding.text,
        "riskHint": grounding.risk_hint or None,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                url,
                json=payload,
                headers={"X-Trace-Secret": settings.TRACE_SECRET or ""},
            )
        resp.raise_for_status()
        research = ResearchLayer.model_validate(resp.json())
        # divagent stamps model/generatedAt; keep its values but never let them be
        # missing (older/leaner responses degrade gracefully).
        research.model = research.model or model_label
        research.generatedAt = research.generatedAt or generated_at
        model_label = research.model or model_label
    except Exception as exc:  # never drop the layer — degrade to the pattern.
        log_event(
            "research_prediction_failure",
            trace_id=trace_id,
            ticker=ticker,
            severity="HIGH",
            model=model_label,
            error=str(exc),
        )
        research = _fallback(pattern, model_label, generated_at)

    log_event(
        "research_prediction_done",
        trace_id=trace_id,
        ticker=ticker,
        model=research.model,
        confidence=research.confidence,
        will_maintain=research.willMaintainPattern,
    )
    return research
