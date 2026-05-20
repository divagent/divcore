# app/integrations/openai_embedder.py
from typing import List

from app.llm.gemini_embedder import embed_fn_gemini

# Original OpenAI setup kept for reference:
# from openai import AsyncOpenAI
# from app.config import get_settings_singleton
#
# settings = get_settings_singleton()
# client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
# EMBED_MODEL = "text-embedding-3-small"  # supports custom dimensions


async def embed_fn(text: str) -> List[float]:
    return await embed_fn_gemini(text, dimension=768)
