# db.py
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from app.config import get_settings_singleton
settings = get_settings_singleton()

async_engine = create_async_engine(settings.DIV_AIVEN_ADMIN,  pool_pre_ping=True,echo=False,)

# 原有的get_db（raw connection）
async def get_db() -> AsyncGenerator[AsyncConnection, None]:
    async with async_engine.begin() as conn:
        yield conn

# 自动事务版 connection context manager
@asynccontextmanager
async def get_db_auto() -> AsyncGenerator[AsyncConnection, None]:
    """自动事务版：自动管理事务提交/回滚"""
    async with async_engine.begin() as conn:
        yield conn
            
            
            











        
# # main.py 或 route.py
# from fastapi import FastAPI, Depends
# from .db import get_db, get_db_auto

# app = FastAPI()

# # 1. 使用原来的get_db（需要手动事务）
# @app.post("/users/manual")
# async def create_user_manual(
#     name: str,
#     db = Depends(get_db)
# ):
#     # 必须手动开始事务
#     async with db.begin():
#         # 你的业务代码
#         from .models import User
#         db.add(User(name=name))
#     return {"message": "created with manual transaction"}

# # 2. 使用get_db_auto（自动事务）
# @app.post("/users/auto")
# async def create_user_auto(
#     name: str,
#     db = Depends(get_db_auto)  # ← 使用auto版本
# ):
#     # 不需要手动begin()，直接操作
#     from .models import User
#     db.add(User(name=name))
#     # 函数正常结束时自动提交
#     return {"message": "created with auto transaction"}


# 核心区别
# 特性	get_db	get_db_auto
# 事务管理	手动（需要async with db.begin():）	自动（已包含在函数内）
# 提交	手动调用await db.commit()	自动提交（无异常时）
# 回滚	手动调用await db.rollback()	自动回滚（异常时）
# 适合场景	需要精细控制事务边界	大多数CRUD操作
# 建议用法
