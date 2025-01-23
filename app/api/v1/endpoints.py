from datetime import datetime


import requests
from app.core.configurate import SessionLocal, scheduler
from apscheduler.triggers.interval import IntervalTrigger
from db.models import Product
from fastapi import FastAPI, HTTPException, Depends,APIRouter
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

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
        from_attributes = True  # Заменили orm_mode на from_attributes


async def get_db():
    async with SessionLocal() as session:
        yield session

@router.post("/api/v1/products", response_model=ProductResponse)
async def add_product(request: ProductRequest, db: AsyncSession = Depends(get_db)):
    product_data = fetch_product_data(request.artikul)
    product = await db.get(Product, request.artikul)
    if product:
        product.name = product_data["name"]
        product.price = product_data["price"]
        product.rating = product_data["rating"]
        product.stock_quantity = product_data["stock_quantity"]
    else:
        product = Product(**product_data)
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product

@router.get("/api/v1/subscribe/{artikul}")
async def subscribe_product(artikul: int, db: AsyncSession = Depends(get_db)):
    scheduler.add_job(fetch_and_store_product, args=[artikul], kwargs={"db": db}, trigger=IntervalTrigger(minutes=30), id=str(artikul), replace_existing=True)
    return {"message": f"Subscription started for artikul {artikul}"}

async def fetch_and_store_product(artikul: int, db: AsyncSession):
    product_data = fetch_product_data(artikul)
    product = await db.get(Product, artikul)
    if product:
        product.name = product_data["name"]
        product.price = product_data["price"]
        product.rating = product_data["rating"]
        product.stock_quantity = product_data["stock_quantity"]
    else:
        product = Product(**product_data)
    db.add(product)
    await db.commit()

# Fetch Product Data Helper

def fetch_product_data(artikul: int):
    url = f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={artikul}"
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Product not found on Wildberries")
    data = response.json()
    product = data["data"]["products"][0]
    return {
        "artikul": artikul,
        "name": product["name"],
        "price": product["salePriceU"] / 100,
        "rating": product.get("rating", 0),
        "stock_quantity": sum(s["qty"] for s in product.get("sizes", []))
    }