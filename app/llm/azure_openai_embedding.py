# app/integrations/azure_openai_embedder.py
from typing import List

from app.llm.gemini_embedder import embed_fn_gemini

# Original Azure/OpenAI setup kept for reference:
# from openai import AsyncOpenAI
# from app.config import get_settings_singleton
#
# settings = get_settings_singleton()
# api_key=settings.OPENAI_API_KEY,
# client = AsyncOpenAI(
#     api_key=settings.OPENAI_API_KEY,
#     base_url="https://haystacked.openai.azure.com/openai/v1/",
# )
# EMBED_DEPLOYMENT = "text-embedding-3-small"
#
# async def embed_fn_azure_new_v1(text: str) -> List[float]:
#     resp = await client.embeddings.create(
#         model=EMBED_DEPLOYMENT,
#         input=text,
#     )
#     return resp.data[0].embedding

async def embed_fn_azure_new_v1(text: str) -> List[float]:
    return await embed_fn_gemini(text)
