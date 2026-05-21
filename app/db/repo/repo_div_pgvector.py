# app/repositories/wage_embedding_repository.py
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import select, insert, update
from typing import List, Dict
from app.db.models.m_div import Div, DivChunk768 as DivChunk


class DivEmbeddingRepository:

    @staticmethod
    async def bulk_insert_embeddings(
        db: AsyncConnection,
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

        if values:
            await db.execute(insert(DivChunk), values)
        # ORM/session style was:
        # db.add_all([DivChunk(**v) for v in values])
        # await db.commit()


    @staticmethod
    async def update_embedding(
        db: AsyncConnection,
        row_id,
        embedding: list[float],
    ):
        await db.execute(
            update(DivChunk)
            .where(DivChunk.id == row_id)
            .values(embedding=embedding)
        )
        # ORM/session style was:
        # row = await db.get(DivChunk, row_id)
        # row.embedding = embedding
        # db.add(row)


    @staticmethod
    async def fetch_div_pgvector(session, limit: int | None = None):
        limit = 500 if limit is None else limit
        
        stmt = select(DivChunk.__table__)
        if limit:
            stmt = stmt.limit(limit)
        res = await session.execute(stmt)
        # ORM/session style was:
        # stmt = select(DivChunk)
        # return res.scalars().all()
        return [dict(row) for row in res.mappings().all()]
