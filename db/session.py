from sqlalchemy.ext.asyncio import AsyncSession
from app.core.configurate import SessionLocal

async def get_db():
    async with SessionLocal() as session:
        yield session
