import aiohttp
import logging
from fastapi import HTTPException

# Настройка логирования
logging.basicConfig(level=logging.INFO)

async def fetch_product_data(artikul: int):
    """Получение данных о продукте с API Wildberries"""
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
