from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.llm.azure_openai_embedding import embed_fn_azure_new_v1
from app.db.models.m_div import Div, DivChunk768 as DivChunk
from app.db.repo.repo_div_pgvector import DivEmbeddingRepository


class EmbeddingService:

    @staticmethod   
    async def embed_all_dummy(
        db: AsyncSession,
    ) -> int:
        rows = await DivEmbeddingRepository.fetch_div_pgvector(db)

        for r in rows:
            text = r.content  # or combine EN + FR if you want
            emb = await embed_fn_azure_new_v1(text)
            await DivEmbeddingRepository.update_embedding(db, r.id, emb)

        await db.commit()
        return len(rows)