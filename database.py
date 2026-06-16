import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from collections.abc import AsyncGenerator
from sqlalchemy.orm import DeclarativeBase

DB_URL = os.getenv("DB_URL", "postgresql+psycopg://postgres:password@localhost:5432/article_db")


engine = create_async_engine(
    DB_URL,
    pool_size = 10,
    max_overflow = 20,
    pool_pre_ping = True,
    pool_recycle=1800,
    echo = False
)


SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

async def get_session()->AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session