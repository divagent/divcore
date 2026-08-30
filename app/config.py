# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from functools import lru_cache


class _Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env",env_file_encoding="utf-8",extra="ignore",)
    # Settings must not be instantiated directly.
    # Always use get_settings_singleton() to access application configuration.
    #     Settings 是实现细节，不是公共 API
    # 公共 API 只有 get_settings_singleton()
    AZURE_SEARCH_ENDPOINT: str = "https://aisearch8.search.windows.net"
    GOOGLE_SHEET_URL: str= "https://docs.google.com/spreadsheets/d/15QBf76ab4zSt-S-oGSrSpgdJngpdGCxFMJqZkC6_sAM/export?format=csv"
    NASDAQ_URL: str= "https://api.nasdaq.com/api/calendar/dividends"

    GOOGLE_PROJECT_ID: str = "divcalendar-507102"
    
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_API_KEY_OPHIR: Optional[str] = None
    # Original OpenAI/Azure settings kept for reference:
    # OPENAI_API_KEY: Optional[str] = None
    # AZURE_OPENAI_API_KEY: Optional[str] = None

    
    SERPERDEV_API_KEY: Optional[str] = None
    TAVILY_API_KEY: str = "ff"
    ALPHAVANTAGE_API_KEY:  str = "ff"
    EOD_API_KEY:  str = "ff"
    FINNHUB_API_KEY:  str = "ff"

    # Google Calendar (predicted-dividend publishing) — see followup.md
    GOOGLE_OAUTH_CLIENT_ID: Optional[str] = "590057077351-seft0saimg261h13i3o8us7cpam5bkc8.apps.googleusercontent.com"
    GOOGLE_OAUTH_CLIENT_SECRET: Optional[str] = None
    GOOGLE_OAUTH_REFRESH_TOKEN: Optional[str] = None
    GOOGLE_CALENDAR_ID: Optional[str] = None

    # Database
    DIV_AIVEN_ADMIN: str = "postgresql+asyncpg://username:pwd@local/icedb"
    DIV_AIVEN_RLS: str = "postgresql+asyncpg://username:pwd@local/icedb"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False


    # Seed Data
    SEED_DATA: bool = True  # Whether to seed data on startup
    SEED_TYPE: str = "full"  # 'full', 'test', or 'none'
    SEED_SAMPLE_SIZE: int = 10  # Number of sample records to create
    
    ADMIN_PASSWORD: str = "admin123"  # Default admin password for seeding (change in production)

    # Application
    PROJECT_NAME: str = "Dividend - FA Cloud"
    VERSION: str = "26.2.11"
    DESCRIPTION: str = "Dividend investing, systematically enhanced."
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"


@lru_cache()
def get_settings_singleton()-> _Settings:
    return _Settings()
