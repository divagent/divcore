import os
from functools import lru_cache

from google import genai

from app.config import get_settings_singleton


DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


@lru_cache(maxsize=1)
def get_gemini_client() -> genai.Client:
    # Prod sets a real env var; locally fall back to the .env-backed settings so
    # dev and deployment behave the same.
    key = os.getenv("GEMINI_API_KEY") or get_settings_singleton().GEMINI_API_KEY
    return genai.Client(api_key=key)
