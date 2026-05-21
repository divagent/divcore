from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import select, delete, insert

from app.db.models.m_div import Div, DivChunk768 as DivChunk
from app.util.div2content import div_to_content


class DividendChunkService:
    def __init__(self, db: AsyncConnection):
        self.db = db

    async def rebuild_chunks(self) -> dict:
        # 1️⃣ Clean chunks
        await self.db.execute(delete(DivChunk))
        # ORM/session style was: await self.db.commit()

        # 2️⃣ Load dividends
        result = await self.db.execute(select(Div.__table__))
        dividends = [dict(row) for row in result.mappings().all()]
        # ORM/session style was:
        # result = await self.db.execute(select(Div))
        # dividends = result.scalars().all()

        # 3️⃣ Build chunks
        chunks: list[dict] = []
        for div in dividends:
            chunks.append(
                {
                    "div_id": div["id"],
                    "chunk_index": 0,
                    "content": div_to_content(div),
                    "embedding": None,
                }
            )

            # ORM/session style was:
            # chunk = DivChunk(div_id=div.id, ...)
            # chunks.append(chunk)

        if chunks:
            await self.db.execute(insert(DivChunk), chunks)
        # ORM/session style was:
        # self.db.add_all(chunks)
        # await self.db.commit()

        return {
            "dividends_processed": len(dividends),
            "chunks_created": len(chunks),
        }
