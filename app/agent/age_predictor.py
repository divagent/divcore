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
from datetime import date

from app.agent.age_tools import get_dividend_data_tool, search_web_tool
from app.agent.agent_schema import DividendPrediction
from app.llm.azure_openai_chat import chat_completion_agent
from app.core.ai_logging import log_event


PREDICTION_SYSTEM_PROMPT = (
    "You are an elite dividend-forecasting analyst. Using the HISTORY and NEWS "
    "context provided, predict the company's NEXT dividend. Respond ONLY with a "
    "single JSON object, no prose, matching exactly this schema:\n"
    "{\n"
    '  "predicted_amount": number|null,   // per-share amount, null if unknowable\n'
    '  "predicted_ex_date": "YYYY-MM-DD"|null,  // next ex-dividend date\n'
    '  "direction": "up"|"down"|"constant",     // vs. the most recent dividend\n'
    '  "confidence": number,              // 0.0-1.0\n'
    '  "reasoning": string                // 1-3 sentences citing the evidence\n'
    "}\n"
    "Rules: base amount/direction on the historical cadence and any confirmed "
    "announcement in the news. If the pattern is weak, irregular, or the company "
    "recently signaled a cut/suspension, still answer but LOWER the confidence and "
    "say why in reasoning. Never refuse. Never invent sources."
)


async def predict_dividend(symbol: str, trace_id: str = "internal") -> DividendPrediction:
    """Run the prediction pipeline for a single ticker and return a validated verdict."""
    symbol = (symbol or "").strip().upper()
    today = date.today().isoformat()
    log_event("predict_dividend_start", trace_id=trace_id, symbol=symbol)

    # (a) history from the internal RAG store
    history = await get_dividend_data_tool(
        f"dividend history, payout cadence and reliability for {symbol}"
    )
    # (b) recent news / announcements from the live web
    news = await search_web_tool(
        f"{symbol} dividend announcement next ex-dividend date and amount {date.today().year}"
    )

    sources: list[str] = []
    for result in (history, news):
        for src in result.get("sources", []) or []:
            if isinstance(src, str) and src not in sources:
                sources.append(src)

    history_text = history.get("data") or history.get("error") or "No history available."
    news_text = news.get("data") or news.get("error") or "No recent news found."

    user_content = (
        f"Today is {today}. Predict the next dividend for {symbol}.\n\n"
        f"=== HISTORY (internal database) ===\n{history_text}\n\n"
        f"=== NEWS (live web) ===\n{news_text}"
    )

    messages = [
        {"role": "system", "content": PREDICTION_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    raw = await chat_completion_agent(messages=messages)

    try:
        data = json.loads(raw)
        prediction = DividendPrediction(
            symbol=symbol,
            predicted_amount=data.get("predicted_amount"),
            predicted_ex_date=data.get("predicted_ex_date"),
            direction=data.get("direction", "constant"),
            confidence=float(data.get("confidence", 0.0) or 0.0),
            reasoning=data.get("reasoning", "") or "",
            sources=sources,
        )
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        # Never drop a prediction: emit a LOW-confidence fallback with the reason.
        log_event(
            "predict_dividend_parse_failure",
            trace_id=trace_id,
            symbol=symbol,
            severity="HIGH",
            error=str(exc),
        )
        prediction = DividendPrediction(
            symbol=symbol,
            direction="constant",
            confidence=0.0,
            reasoning=(
                "Could not derive a structured forecast from the available data; "
                "returned as LOW confidence rather than dropping the prediction."
            ),
            sources=sources,
        )

    log_event(
        "predict_dividend_done",
        trace_id=trace_id,
        symbol=symbol,
        direction=prediction.direction,
        confidence=prediction.confidence,
        confidence_label=prediction.confidence_label,
    )
    return prediction
