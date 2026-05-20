import os
from functools import lru_cache

from google import genai


DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


@lru_cache(maxsize=1)
def get_gemini_client() -> genai.Client:
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])
