from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import logging
from app.core.configurate import SessionLocal
from sqlalchemy.future import select
from app.api.v1.utils import fetch_product_data  # Импорт из utils.py
from db.models import Product
from datetime import datetime
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

# Инициализация планировщика
scheduler = AsyncIOScheduler()

# Настройка логирования
logging.basicConfig(level=logging.INFO)


# Конфигурация хранилища задач для персистентности
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')  # Или используйте вашу БД
}

def load_jobs():
    """Загружаем все задачи, сохраненные в базе данных."""
    scheduler.resume()  # Восстанавливаем задачи
    logging.info("Scheduler jobs resumed from database.")

scheduler = AsyncIOScheduler(jobstores=jobstores)

async def scheduled_product_update(artikul: int):
    async with SessionLocal() as db:
        result = await db.execute(select(Product).filter(Product.artikul == artikul))
        product = result.scalar_one_or_none()
        if product:
            updated_product = await fetch_product_data(artikul)
            product.name = updated_product["name"]
            product.price = updated_product["salePriceU"] / 100
            product.rating = updated_product.get("reviewRating", 0)
            product.stock_quantity = sum(
                stock["qty"]
                for size in updated_product.get("sizes", [])
                for stock in size.get("stocks", [])
            )

            # Принудительное обновление времени
            product.updated_at = datetime.utcnow()

            # Сохраняем изменения в базе данных
            await db.commit()
            logging.info(f"Product {artikul} updated successfully at {datetime.utcnow()}")
        else:
            logging.warning(f"Product with artikul {artikul} not found in database")


def job_listener(event):
    """Слушатель событий для логирования выполнения задач."""
    if event.exception:
        logging.error(f"Job {event.job_id} failed")
    else:
        logging.info(f"Job {event.job_id} executed successfully")


# Добавляем слушатель событий и запускаем планировщик
scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
scheduler.start()
