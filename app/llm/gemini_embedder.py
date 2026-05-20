from typing import List
from google.genai import types

from google import genai
client = genai.Client()


async def embed_fn_gemini(text: str, dimension: int=768) -> List[float]:
    response = await client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=dimension)
    )

    return response.data[0].embedding
