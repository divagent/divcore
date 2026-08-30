"""Repository for `dividend_predictions` — persisting AI dividend forecasts.

Follows the same Core-statement-on-`AsyncConnection` idiom as `repo_div_inject.py`
(no ORM session; the connection's `begin()` block commits). Upserts on the
`(symbol, predicted_ex_date)` unique constraint so re-forecasting a symbol updates
the existing row instead of duplicating it — mirroring the idempotent calendar event.
"""

import json
from datetime import date
from typing import Any, Optional

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app.agent.agent_schema import DividendPrediction
from app.db.models.m_div import DivPrediction


class DivPredictionRepo:
    def __init__(self, db: AsyncConnection):
        self.db = db

    @staticmethod
    def _to_values(prediction: DividendPrediction, google_event_id: Optional[str]) -> dict[str, Any]:
        ex_date: Optional[date] = (
            date.fromisoformat(prediction.predicted_ex_date)
            if prediction.predicted_ex_date
            else None
        )
        return {
            "symbol": prediction.symbol,
            "predicted_ex_date": ex_date,
            "predicted_amount": prediction.predicted_amount,
            "direction": prediction.direction,
            "confidence": prediction.confidence,
            "reasoning": prediction.reasoning,
            "sources": json.dumps(prediction.sources or []),
            "google_event_id": google_event_id,
        }

    async def upsert_prediction(
        self, prediction: DividendPrediction, google_event_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Insert or update the prediction row; returns the persisted row as a dict.

        Conflict target is the `(symbol, predicted_ex_date)` unique constraint. Note:
        when `predicted_ex_date` is NULL, Postgres treats NULLs as distinct, so such
        (unpublishable) rows are inserted rather than merged — acceptable, since only
        predictions with a real ex-date reach the calendar.
        """
        values = self._to_values(prediction, google_event_id)

        stmt = insert(DivPrediction).values(values)
        update_cols = {
            k: stmt.excluded[k]
            for k in values
            if k not in ("symbol", "predicted_ex_date")
        }
        stmt = stmt.on_conflict_do_update(
            constraint="uq_prediction_symbol_ex_date",
            set_=update_cols,
        ).returning(DivPrediction.__table__)

        result = await self.db.execute(stmt)
        return dict(result.mappings().first())

    async def set_google_event_id(self, row_id: Any, google_event_id: str) -> None:
        """Attach a calendar event id to an already-persisted prediction row."""
        from sqlalchemy import update

        await self.db.execute(
            update(DivPrediction)
            .where(DivPrediction.id == row_id)
            .values(google_event_id=google_event_id)
        )
