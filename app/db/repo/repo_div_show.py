# app/repositories/dividend_repo.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.models.m_div import Div, DivChunk768 as DivChunk
from app.db.models.m_symbols import Symbols


class DivRepository:

    @staticmethod
    async def list_divs(db: AsyncConnection,) -> list[Div]:
        result = await db.execute(select(Div.__table__))
        # ORM/session style was: result = await db.execute(select(Div))
        return result.mappings().all()   # type: ignore[return-value]


    @staticmethod
    async def list_divs_emb(db: AsyncConnection,) -> list[DivChunk]:
        result = await db.execute(select(DivChunk.__table__))
        # ORM/session style was: result = await db.execute(select(DivChunk))
        return result.mappings().all()   # type: ignore[return-value]

    @staticmethod
    async def list_symbols(db: AsyncConnection, limit: int = 1000) -> list[dict]:
        stmt = (
            select(
                Symbols.symbol,
                Symbols.displaySymbol,
                Symbols.type,
                Symbols.currency,
            )
            .order_by(Symbols.symbol.asc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return [dict(row) for row in result.mappings().all()]

    @staticmethod
    async def list_divs_by_symbol(db: AsyncConnection, symbol: str) -> list[dict]:
        stmt = (
            select(Div.__table__)
            .where(Div.symbol == symbol.upper())
            .order_by(Div.dividend_ex_date.asc())
        )
        result = await db.execute(stmt)
        return [dict(row) for row in result.mappings().all()]
