# app/integrations/openai_embedder.py
from typing import List
from openai import AsyncOpenAI
from app.config import get_settings_singleton

settings = get_settings_singleton()

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

EMBED_MODEL = "text-embedding-3-small"  # supports custom dimensions


async def embed_fn(text: str) -> List[float]:
    response = await client.embeddings.create(
        model=EMBED_MODEL,
        input=text,
        dimensions=1536,  
    )

    return response.data[0].embedding
