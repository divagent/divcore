# db.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession,async_sessionmaker,create_async_engine

from app.config import get_settings_singleton
settings = get_settings_singleton()

async_engine = create_async_engine(
    settings.DIV_ASYNC,
    pool_pre_ping=True,
    echo=False,  # True only in local dev
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    expire_on_commit=False,
)

# 原有的get_db（裸session，需要手动管理事务）
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
        
        
# 新增的get_db_auto（自动事务管理）
AsyncSessionFactory = async_sessionmaker(async_engine, expire_on_commit=False,)
async def get_db_auto() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        try:
            # 关键：自动开始事务
            async with session.begin():
                yield session
            # 这里自动提交（如果没有异常）
        except Exception:
            # 这里自动回滚（session.begin()自动处理）
            raise
        finally:
            await session.close()
            
            
            


