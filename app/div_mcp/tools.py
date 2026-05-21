from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.models.m_div import Div


def serialize_dividend(row: Div) -> dict[str, Any]:
    def field(name: str):
        if isinstance(row, dict):
            return row.get(name)
        return getattr(row, name)

    def clean(value):
        if isinstance(value, (date,)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        return value

    return {
        "id": str(field("id")),
        "company_name": field("company_name"),
        "symbol": field("symbol"),
        "dividend_ex_date": clean(field("dividend_ex_date")),
        "record_date": clean(field("record_date")),
        "payment_date": clean(field("payment_date")),
        "dividend_rate": clean(field("dividend_rate")),
        "indicated_annual_dividend": clean(field("indicated_annual_dividend")),
        "announcement_date": clean(field("announcement_date")),
        "latest_price": clean(field("latest_price")),
        "yield_percent": clean(field("yield_percent")),
        "market_cap": clean(field("market_cap")),
        "div_type": field("div_type"),
        "company_type": field("company_type"),
    }


async def get_dividend_snapshot(
    db: AsyncConnection,
    limit: int = 100,
) -> dict[str, Any]:
    result = await db.execute(
        select(Div.__table__)
        .order_by(Div.dividend_ex_date.asc(), Div.symbol.asc())
        .limit(limit)
    )
    rows = [dict(row) for row in result.mappings().all()]
    # ORM/session style was:
    # result = await db.execute(select(Div).order_by(...).limit(limit))
    # rows = result.scalars().all()

    return {
        "count": len(rows),
        "items": [serialize_dividend(row) for row in rows],
    }
