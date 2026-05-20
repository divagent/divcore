# app/services/indexing_service.py
from app.db.repo.repo_div_pgvector import DivEmbeddingRepository
from app.providers.az_search_client import get_search_client

BATCH_SIZE = 500

async def bulk_index_dividends(db_session):
    chunks = await DivEmbeddingRepository.fetch_div_pgvector(db_session)
    search_client = get_search_client()

    batch = []
    for c in chunks:
        batch.append({
            "id": str(c.id),
            "pg_id": str(c.div_id),
            "chunk_text": c.content,
            "embedding": c.embedding.tolist(),
        })

        if len(batch) >= BATCH_SIZE:
            await search_client.upload_documents(batch)
            batch.clear()

    if batch:
        await search_client.upload_documents(batch)
