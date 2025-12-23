"""
数据库连接和会话管理
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from ..config import settings
from .models import Base


# 异步引擎
async_engine = create_async_engine(
    settings.MYSQL_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# 同步引擎(用于初始化数据库等操作)
sync_engine = create_engine(
    settings.MYSQL_URL_SYNC,
    echo=settings.DEBUG,
    pool_pre_ping=True
)

# 同步会话工厂
SyncSessionLocal = sessionmaker(
    sync_engine,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话(异步)"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话上下文管理器"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """初始化数据库(创建表)"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库连接"""
    await async_engine.dispose()


def init_db_sync():
    """同步初始化数据库"""
    Base.metadata.create_all(bind=sync_engine)
