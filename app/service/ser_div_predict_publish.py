"""Orchestrator: predict a dividend, persist it, and publish it to the calendar.

Ties the two halves together:
    age_predictor.predict_dividend  ->  DivPredictionRepo (dividend_predictions)
                                    ->  ser_gcal_publish.publish_prediction

Flow per symbol:
  1. `predict_dividend(symbol)` — never fails; low-signal yields a LOW-confidence verdict.
  2. If there is a `predicted_ex_date`, publish an (idempotent) all-day calendar event.
     A publish failure is logged but does NOT abort persistence — we still record the
     forecast.
  3. Upsert the prediction into `dividend_predictions`, storing the `google_event_id`.

The Google publish uses a blocking client, so it is run in a worker thread
(`asyncio.to_thread`) to avoid stalling the event loop.
"""

import asyncio
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncConnection

from app.agent.age_predictor import predict_dividend
from app.core.ai_logging import log_event
from app.db.repo.repo_div_prediction import DivPredictionRepo
from app.service.ser_gcal_publish import (
    CalendarNotConfigured,
    publish_prediction,
)


async def predict_and_publish(
    symbol: str, db: AsyncConnection, *, trace_id: str = "internal"
) -> dict[str, Any]:
    """Predict, publish (if datable), and persist one symbol. Returns a summary dict."""
    prediction = await predict_dividend(symbol, trace_id=trace_id)

    google_event_id: Optional[str] = None
    published = False
    publish_error: Optional[str] = None

    if prediction.predicted_ex_date:
        try:
            event = await asyncio.to_thread(
                publish_prediction, prediction, trace_id=trace_id
            )
            google_event_id = event.get("id")
            published = True
        except CalendarNotConfigured as exc:
            publish_error = str(exc)
            log_event(
                "predict_publish_calendar_unconfigured",
                trace_id=trace_id,
                symbol=prediction.symbol,
                severity="MEDIUM",
            )
        except Exception as exc:  # keep persisting even if the calendar write fails
            publish_error = str(exc)
            log_event(
                "predict_publish_calendar_failure",
                trace_id=trace_id,
                symbol=prediction.symbol,
                severity="HIGH",
                error=str(exc),
            )

    repo = DivPredictionRepo(db)
    row = await repo.upsert_prediction(prediction, google_event_id=google_event_id)

    log_event(
        "predict_publish_done",
        trace_id=trace_id,
        symbol=prediction.symbol,
        published=published,
        google_event_id=google_event_id,
        prediction_id=str(row.get("id")),
    )

    return {
        "symbol": prediction.symbol,
        "prediction": prediction.model_dump(),
        "prediction_id": str(row.get("id")),
        "published": published,
        "google_event_id": google_event_id,
        "publish_error": publish_error,
    }
