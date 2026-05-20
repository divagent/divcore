from typing import List
from google.genai import types

from app.llm.gemini import get_gemini_client


async def embed_fn_gemini(text: str, dimension: int=768) -> List[float]:
    response = await get_gemini_client().aio.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=dimension)
    )

    if hasattr(response, "embeddings"):
        return response.embeddings[0].values
    return response.data[0].embedding
