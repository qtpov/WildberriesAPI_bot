from datetime import datetime
import logging
import aiohttp
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from app.core.configurate import SessionLocal, scheduler
from db.models import Product
from app.api.v1.utils import fetch_product_data  # Импорт из utils.py
# Остальной код без изменений


from app.api.v1.scheduler import scheduled_product_update

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
        from_attributes = True


async def get_db():
    async with SessionLocal() as session:
        yield session


async def add_product_to_db(artikul: int, db: AsyncSession):
    product = await fetch_product_data(artikul)
    stock_quantity = sum(
        stock["qty"] for size in product.get("sizes", []) for stock in size.get("stocks", [])
    )
    new_product = Product(
        artikul=artikul,
        name=product["name"],
        price=product["salePriceU"] / 100,
        rating=product.get("reviewRating", 0),
        stock_quantity=stock_quantity,
    )
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product


@router.post("/api/v1/products", response_model=ProductResponse)
async def add_product(request: ProductRequest, db: AsyncSession = Depends(get_db)):
    try:
        product = await add_product_to_db(request.artikul, db)
        return product
    except HTTPException as e:
        raise e


@router.get("/api/v1/subscribe/{artikul}")
async def subscribe_artikul(
    artikul: int,
    db: AsyncSession = Depends(get_db)
):
    product = await db.execute(select(Product).filter(Product.artikul == artikul))
    if not product.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Product not found in database")

    scheduler.add_job(
        scheduled_product_update,
        trigger=IntervalTrigger(minutes=0.5),
        args=[artikul],
        id=f"update_{artikul}",
        replace_existing=True,
    )
    return {"message": f"Subscription for artikul {artikul} started."}
