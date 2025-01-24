from datetime import datetime
import logging
import aiohttp
from app.core.configurate import SessionLocal, scheduler
from apscheduler.triggers.interval import IntervalTrigger
from db.models import Product
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from sqlalchemy.ext.asyncio import AsyncSession

# Настройка логирования
logging.basicConfig(level=logging.INFO)

router = APIRouter()

class ProductRequest(BaseModel):
    artikul: int

class ProductResponse(BaseModel):
    name: str
    price: float
    rating: float
    stock_quantity: int
    updated_at: datetime

    class Config:
        from_attributes = True  # Замена orm_mode

# Асинхронный генератор сессии базы данных
async def get_db():
    async with SessionLocal() as session:
        yield session

# Асинхронная функция для получения данных с API Wildberries
async def fetch_product_data(artikul: int):
    url = f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={artikul}"
    logging.info(f"Fetching product data for artikul {artikul}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logging.error(f"Failed to fetch product data for artikul {artikul}, status: {response.status}")
                    raise HTTPException(status_code=404, detail="Product not found on Wildberries")
                data = await response.json()
                product = data["data"]["products"][0]
                logging.info(f"Product data fetched for artikul {artikul}")
                return product
    except Exception as e:
        logging.error(f"Error fetching product data for artikul {artikul}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Асинхронная функция для добавления товара в базу данных
async def add_product_to_db(artikul: int, db: AsyncSession):
    product = await fetch_product_data(artikul)
    new_product = Product(
        artikul=artikul,
        name=product["name"],
        price=product["salePriceU"] / 100,
        rating=product.get("reviewRating", 0),
        stock_quantity=product.get("stock_quantity", 0)
    )

    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product

# Эндпоинт для добавления товара в базу данных
@router.post("/api/v1/products", response_model=ProductResponse)
async def add_product(request: ProductRequest, db: AsyncSession = Depends(get_db)):
    try:
        product = await add_product_to_db(request.artikul, db)
        return product
    except HTTPException as e:
        raise e

# Эндпоинт для подписки на обновления товара каждые 30 минут
@router.get("/api/v1/subscribe/{artikul}")
async def subscribe_to_product_updates(artikul: int, db: AsyncSession = Depends(get_db)):
    async def update_product_data():
        try:
            await add_product_to_db(artikul, db)
            logging.info(f"Product {artikul} updated successfully.")
        except Exception as e:
            logging.error(f"Error updating product {artikul}: {e}")

    # Настроим расписание для обновлений каждые 30 минут
    scheduler.add_job(
        update_product_data,
        IntervalTrigger(minutes=30),
        id=f"update_{artikul}",
        replace_existing=True
    )

    # Запускаем обновление сразу при подписке
    await update_product_data()

    return {"message": f"Subscribed to updates for product {artikul} every 30 minutes."}

# Функция для обновления всех товаров через расписание (по условию задачи)
@scheduler.scheduled_job(IntervalTrigger(minutes=30))
async def scheduled_product_update():
    async with SessionLocal() as db:
        products = await db.execute(Product.__table__.select())
        for product in products:
            await add_product_to_db(product.artikul, db)
            logging.info(f"Updated product {product.artikul} in database")

