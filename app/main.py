from app.core.configurate import Base, engine
from fastapi import FastAPI
from app.api.v1.endpoints import router as api_app
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.api.v1.scheduler import scheduler, load_jobs
app = FastAPI()

# Включаем маршруты из других частей проекта
app.include_router(api_app, prefix="/api/v1", tags=["products"])

# Планировщик задач (если он используется в другом месте)
scheduler = AsyncIOScheduler()


@app.on_event("startup")
async def startup():
    # Инициализация базы данных
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Загружаем задачи при старте приложения
    load_jobs()
    # Запуск планировщика
    scheduler.start()


@app.on_event("shutdown")
async def shutdown():
    # Остановка планировщика
    scheduler.shutdown()
