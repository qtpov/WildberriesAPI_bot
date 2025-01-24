import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.core.configurate import BOT_TOKEN
from db.models import Product, Subscription
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import aiohttp
from bot.keyboards.inline import get_keyboard_start,create_subscribe_button
from app.core.configurate import SessionLocal

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Определение состояния для FSM
class FindArtikul(StatesGroup):
    choosing_artikul_for_get = State()
    choosing_artikul_for_add = State()

# Функция для получения сессии базы данных
async def get_db():
    async with SessionLocal() as db:
        yield db


# Хендлер для команды /start
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Здравствуйте, для продолжения используйте кнопку.", reply_markup=get_keyboard_start())

# Хендлер для кнопки "Получить данные по товару"
@dp.callback_query(F.data == 'get_artikul')
async def get_art(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Пришлите артикул.")
    await callback.answer()  # Закрываем callback
    await state.set_state(FindArtikul.choosing_artikul_for_get)  # Переход в состояние выбора артикула

# Хендлер для кнопки "Добавить товар в базу (Админ)"
@dp.callback_query(F.data == 'add_product')
async def add_product(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Отправьте артикул для добавления в базу.")
    await callback.answer()  # Закрываем callback
    await state.set_state(FindArtikul.choosing_artikul_for_add)  # Переход в состояние выбора артикула

# Функция для получения данных о товаре из базы через SQLAlchemy

async def get_product_from_db(artikul: int, db: AsyncSession):
    try:
        result = await db.execute(select(Product).filter(Product.artikul == artikul))
        product = result.scalar_one_or_none()
        if product:
            logging.info(f"Product with artikul {artikul} found in database.")
            return {
                "name": product.name,
                "price": product.price,
                "rating": product.rating,
                "stock_quantity": product.stock_quantity
            }
        logging.info(f"Product with artikul {artikul} not found in database.")
        return None
    except Exception as e:
        logging.error(f"Error fetching product with artikul {artikul}: {e}")
        return None

# Функция для добавления товара в базу через API
async def add_product_to_db(artikul: int, db: AsyncSession):
    # Сначала проверяем, есть ли товар в базе
    existing_product = await get_product_from_db(artikul, db)
    if existing_product:
        # Если товар уже есть в базе, не добавляем его
        logging.info(f"Product with artikul {artikul} already exists in database.")
        return existing_product

    # Если товара нет в базе, пытаемся получить данные через API
    url = f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={artikul}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if not data["data"]["products"]:
                        logging.error(f"No product data found for artikul {artikul}.")
                        return None
                    product = data["data"]["products"][0]
                    product_data = {
                        "artikul": artikul,
                        "name": product["name"],
                        "price": product["salePriceU"] / 100,
                        "rating": product.get("reviewRating", 0),
                        "stock_quantity": sum(
                            stock['qty'] for size in product.get("sizes", []) for stock in size.get("stocks", []))
                    }

                    # Сохраняем данные в базу
                    product_in_db = Product(**product_data)
                    db.add(product_in_db)
                    await db.commit()
                    await db.refresh(product_in_db)
                    logging.info(f"Product with artikul {artikul} added to database.")
                    return product_data
                else:
                    logging.error(f"Failed to fetch product data from API for artikul {artikul}.")
                    return None
    except Exception as e:
        logging.error(f"Error fetching product data from API: {e}")
        return None


# Хендлер для получения артикула и работы с базой данных
@dp.message(FindArtikul.choosing_artikul_for_get)
async def get_product_data(message: types.Message, state: FSMContext):
    async with SessionLocal() as db:
        try:
            artikul = int(message.text.strip())  # Преобразуем в int

            # Проверка, есть ли товар в базе данных
            product_data = await get_product_from_db(artikul, db)

            if product_data == None:
                await message.answer("Товар с таким артикулом не найден.")
            else:
                # Если данные найдены, выводим их пользователю
                await message.answer(
                    f"Название товара: {product_data['name']}\n"
                    f"Артикул: {artikul}\n"
                    f"Цена: {product_data['price']} руб.\n"
                    f"Рейтинг товара: {product_data['rating']}\n"
                    f"Количество на складе: {product_data['stock_quantity']}",
                    reply_markup=create_subscribe_button(artikul)  # Добавляем кнопку подписки
                )

            await state.clear()  # Очищаем состояние
        except ValueError:
            await message.answer("Пожалуйста, отправьте правильный артикул (число).")
            await state.clear()

# Хендлер для получения артикула и работы с базой данных
@dp.message(FindArtikul.choosing_artikul_for_add)
async def add_product_data(message: types.Message, state: FSMContext):
    async with SessionLocal() as db:
        try:
            artikul = int(message.text.strip())  # Преобразуем в int

            # Проверка, есть ли товар в базе данных
            product_data = await get_product_from_db(artikul, db)

            if not product_data:
                # Если товара нет, пытаемся добавить его в базу через API
                added_product = await add_product_to_db(artikul, db)
                if added_product:
                    product_data = added_product
                    await message.answer(
                        f"Новый товар успешно добавлен!\n"
                        f"Название товара: {product_data['name']}\n"
                        f"Артикул: {artikul}\n"
                        f"Цена: {product_data['price']} руб.\n"
                        f"Рейтинг товара: {product_data['rating']}\n"
                        f"Количество на складе: {product_data['stock_quantity']}",
                        reply_markup=create_subscribe_button(artikul)
                    )
                else:
                    await message.answer("Не удалось добавить товар")
                    await state.clear()
                    return
            else:
                await message.answer("Товар с таким артикулом уже есть в базе.")

            await state.clear()  # Очищаем состояние

        except ValueError:
            await message.answer("Пожалуйста, отправьте правильный артикул (число).")
            await state.clear()

# Хендлер для подписки
@dp.callback_query(F.data.startswith("subscribe_"))
async def handle_subscribe(callback_query: types.CallbackQuery, state: FSMContext):
    artikul = int(callback_query.data.split("_")[1])

    async with SessionLocal() as db:
        result = await db.execute(select(Product).filter(Product.artikul == artikul))
        product = result.scalar_one_or_none()
        if not product:
            await callback_query.message.answer("Продукт не найден.")
        else:
            # Создаем подписку
            subscription = Subscription(user_id=callback_query.from_user.id, artikul=artikul)
            db.add(subscription)
            await db.commit()

            await callback_query.message.answer(f"Подписка на {product.name} оформлена.")
    await callback_query.answer()


# Основная функция для запуска бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
