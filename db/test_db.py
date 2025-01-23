from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "postgresql+asyncpg://postgres:pa$$word@localhost/wildberries"

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession)

Base = declarative_base()

async def test_connection():
    async with engine.begin() as conn:
        print("Подключение к базе данных установлено успешно!")
        await conn.run_sync(Base.metadata.create_all)

import asyncio
asyncio.run(test_connection())
