# app/repositories/wage_embedding_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict
from app.db.models.m_div import Div, DivChunk768 as DivChunk


class DivEmbeddingRepository:

    @staticmethod
    async def bulk_insert_embeddings(
        db: AsyncSession,
        embeddings: List[Dict],
    ) -> None:
        """
        embeddings: list of dicts with keys: source_id, chunk, embedding (list[float])
        """
        # use raw insert for pgvector
        values = [
            {
                "source_id": e["source_id"],
                "chunk_en": e["chunk_en"],
                "chunk_fr": e["chunk_fr"],
                "embedding": e["embedding"],  # as float[]
            }
            for e in embeddings
        ]

        # raw insert example using SQLAlchemy Core

        db.add_all([DivChunk(**v) for v in values])
        await db.commit()


    @staticmethod
    async def update_embedding(
        db: AsyncSession,
        row_id,
        embedding: list[float],
    ):
        row = await db.get(DivChunk, row_id)
        row.embedding = embedding    # type: ignore
        db.add(row)


    @staticmethod
    async def fetch_div_pgvector(session, limit: int | None = None):
        limit = 500 if limit is None else limit
        
        stmt = select(DivChunk)
        if limit:
            stmt = stmt.limit(limit)
        res = await session.execute(stmt)
        return res.scalars().all()
