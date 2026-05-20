from azure.search.documents.models import VectorizedQuery
from app.providers.az_search_client import get_search_client
from app.llm.azure_openai_embedding import embed_fn_azure_new_v1

async def search_dividends(query: str, top_k: int):
    query_vec = await embed_fn_azure_new_v1(query)
    search_client = get_search_client()

    vector_query = VectorizedQuery(
        vector=query_vec,
        k=50,
        fields="embedding",
    )

    results = await search_client.search(
        search_text=query,
        vector_queries=[vector_query],
        top=top_k,
    )

    out = []
    async for r in results:
        out.append({
            "id": r["id"],
            "pg_id": r["pg_id"],
            "content": r["chunk_text"],
            "score": r["@search.score"],
        })
    return out
