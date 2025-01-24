import os
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from apscheduler.schedulers.asyncio import AsyncIOScheduler

DATABASE_URL = ""
BOT_TOKEN = ""
Base = declarative_base()
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
scheduler = AsyncIOScheduler()
