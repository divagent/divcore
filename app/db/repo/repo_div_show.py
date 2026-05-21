# app/repositories/dividend_repo.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.models.m_div import Div, DivChunk768 as DivChunk


class DivRepository:

    @staticmethod
    async def list_divs(db: AsyncConnection,) -> list[Div]:
        result = await db.execute(select(Div))
        return result.mappings().all()   # type: ignore[return-value]


    @staticmethod
    async def list_divs_emb(db: AsyncConnection,) -> list[DivChunk]:
        result = await db.execute(select(DivChunk))
        return result.mappings().all()   # type: ignore[return-value]
