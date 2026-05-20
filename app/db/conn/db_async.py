# db.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession,async_sessionmaker,create_async_engine

from app.config import get_settings_singleton
settings = get_settings_singleton()
DB_URL = settings.DIV_ADMIN

async_engine = create_async_engine(DB_URL,pool_pre_ping=True,echo=False, )

async def get_db():
    async with async_engine.begin() as conn:
        yield conn
        