# app/repositories/dividend_repo.py
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.m_div import Div, DivChunk768 as DivChunk


class DivRepository:

    @staticmethod
    async def list_divs(
        db: AsyncSession,
    ) -> list[Div]:
        result = await db.execute(select(Div))
        return result.scalars().all()   # type: ignore[return-value]


    @staticmethod
    async def list_divs_emb(
        db: AsyncSession,
    ) -> list[DivChunk]:
        result = await db.execute(select(DivChunk))
        return result.scalars().all()   # type: ignore[return-value]
