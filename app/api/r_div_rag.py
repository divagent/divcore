from fastapi import APIRouter
from app.service.ser_ai_rag import rag_query_contract, rag_query

ragRou = APIRouter(prefix="/rag", tags=["RAG"])

@ragRou.post("/query-contract")
async def query_rag(payload: dict):
    question = payload["question"]
    top_k = payload.get("top_k", 5)
    return await rag_query_contract(question, top_k)


@ragRou.post("/rebuild-chunks", summary="Rebuild dividend_chunks from dividends",)
async def rebuild_dividend_chunks(
    db: AsyncSession = Depends(get_db),
):
    service = DividendChunkService(db)
    return await service.rebuild_chunks()


@ragRou.post("/embed-all")
async def embed_all_div(db: AsyncSession = Depends(get_db),):
    count = await EmbeddingService.embed_all_dummy(db)
    return {"embedded": count}

