"""Repository for `div_cal_trade` — the calendar-tick + trade-log table.

Core-statement-on-`AsyncConnection` idiom (no ORM session; the connection's
`begin()` block commits). The predict/publish flow upserts the prediction fields
on the `(symbol, ex_date)` unique constraint; the Trades tab reads rows
and patches the user-entered trade fields.
"""

import json
from datetime import date
from typing import Any, Optional

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app.agent.agent_schema import DividendPrediction
from app.db.models.m_div import DivCalTrade

# Only these columns may be patched from the Trades tab. Everything else on the
# row is owned by the predict flow.
EDITABLE_FIELDS = frozenset(
    {
        "company_name",
        "ex_date",  # exposed as the editable "ex-date"
        "payment_date",
        "purchase_date",
        "purchase_amount",
        "sell_date",
        "sell_amount",
        "dividend_amount",
        "hidden",
    }
)


class DivCalTradeRepo:
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
            "ex_date": ex_date,
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
        """Insert or update the prediction fields of the tick's row.

        Conflict target is the `(symbol, ex_date)` unique constraint. Only
        the prediction-owned columns are updated on conflict, so a user's trade
        entries on an existing row are preserved when the tick is re-predicted.
        """
        values = self._to_values(prediction, google_event_id)

        stmt = insert(DivCalTrade).values(values)
        update_cols = {
            k: stmt.excluded[k]
            for k in values
            if k not in ("symbol", "ex_date")
        }
        stmt = stmt.on_conflict_do_update(
            constraint="uq_div_cal_trade_symbol_ex_date",
            set_=update_cols,
        ).returning(DivCalTrade.__table__)

        result = await self.db.execute(stmt)
        return dict(result.mappings().first())

    async def set_google_event_id(self, row_id: Any, google_event_id: str) -> None:
        """Attach a calendar event id to an already-persisted row."""
        await self.db.execute(
            update(DivCalTrade)
            .where(DivCalTrade.id == row_id)
            .values(google_event_id=google_event_id)
        )

    async def list_trades(self, *, include_hidden: bool = False) -> list[dict[str, Any]]:
        """Return every tick/trade row, newest ex-date first. Hidden rows are
        excluded unless `include_hidden` is True."""
        stmt = select(DivCalTrade.__table__)
        if not include_hidden:
            stmt = stmt.where(DivCalTrade.hidden.is_(False))
        stmt = stmt.order_by(DivCalTrade.ex_date.desc().nullslast())
        result = await self.db.execute(stmt)
        return [dict(row) for row in result.mappings().all()]

    async def update_trade(self, row_id: Any, fields: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Patch the user-editable columns of one row. Unknown keys are ignored.
        Returns the updated row, or None if the id doesn't exist / nothing valid
        was supplied."""
        clean = {k: v for k, v in fields.items() if k in EDITABLE_FIELDS}
        if not clean:
            return None
        stmt = (
            update(DivCalTrade)
            .where(DivCalTrade.id == row_id)
            .values(**clean)
            .returning(DivCalTrade.__table__)
        )
        result = await self.db.execute(stmt)
        row = result.mappings().first()
        return dict(row) if row else None
