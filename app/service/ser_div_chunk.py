from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.db.models.m_div import Div, DivChunk768 as DivChunk
from app.util.div2content import div_to_content


class DividendChunkService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def rebuild_chunks(self) -> dict:
        # 1️⃣ Clean chunks
        await self.db.execute(delete(DivChunk))
        await self.db.commit()

        # 2️⃣ Load dividends
        result = await self.db.execute(select(Div))
        dividends = result.scalars().all()

        # 3️⃣ Build chunks
        chunks: list[DivChunk] = []
        for div in dividends:
            chunk = DivChunk(
                div_id=div.id,
                chunk_index=0,
                content=div_to_content(div),
                embedding=None,
            )
            chunks.append(chunk)

        self.db.add_all(chunks)
        await self.db.commit()

        return {
            "dividends_processed": len(dividends),
            "chunks_created": len(chunks),
        }
