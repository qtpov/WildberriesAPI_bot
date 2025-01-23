import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.core.configurate import BOT_TOKEN  # Не забудьте заменить на ваш реальный путь к токену

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Определение состояния для FSM
class FindArtikul(StatesGroup):
    choosing_artikul = State()


# Функция для получения данных о товаре по артикулу из API (асинхронно)
async def get_product_by_artikul(artikul: str):
    # Замените URL на ваш реальный endpoint API
    url = f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={artikul}"

    async with aiohttp.ClientSession() as session:
        # Асинхронный запрос к API
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()  # Получаем JSON ответ от API
            else:
                return None  # Если API вернуло ошибку, возвращаем None


# Клавиатура для стартового сообщения
def get_keyboard_start():
    buttons = [
        [InlineKeyboardButton(text='Получить данные по товару', callback_data='get_artikul')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Хендлер для команды /start
@dp.message(Command("start"))
async def start(message: types.Message):
    # Отправляем стартовое сообщение с кнопкой
    await message.answer("Здравствуйте, для продолжения используйте кнопку.", reply_markup=get_keyboard_start())


# Хендлер для кнопки "Получить данные по товару"
@dp.callback_query(F.data == 'get_artikul')
async def get_art(callback: types.CallbackQuery, state: FSMContext):
    # Отправляем сообщение с просьбой прислать артикул
    await callback.message.answer("Пришлите артикул.")
    await callback.answer()  # Закрываем callback
    await state.set_state(FindArtikul.choosing_artikul)  # Переход в состояние выбора артикула


# Хендлер для получения артикула и запроса данных о товаре
@dp.message(FindArtikul.choosing_artikul)
async def get_product_data(message: types.Message, state: FSMContext):
    artikul = message.text  # Получаем артикул от пользователя
    # Получаем данные о товаре с API
    product_data = await get_product_by_artikul(artikul)

    if product_data:
        # Пытаемся извлечь данные из JSON ответа
        try:
            product = product_data['data']['products'][0]  # Берём первый товар из списка продуктов
            name = product['name']
            price = product['salePriceU'] / 100  # Цена в рублях
            rating = product['rating']
            quantity = sum(stock['qty'] for size in product['sizes'] for stock in size['stocks'])  # Суммируем количество товаров по складам

            # Отправляем информацию о товаре пользователю
            await message.answer(
                f"Название товара: {name}\n"
                f"Артикул: {artikul}\n"
                f"Цена: {price} руб.\n"
                f"Рейтинг товара: {rating}\n"
                f"Количество товара на складах: {quantity}"
            )
        except (KeyError, IndexError) as e:
            await message.answer("Ошибка при обработке данных о товаре.")
    else:
        # Если товар не найден, сообщаем пользователю
        await message.answer("Товар с таким артикулом не найден.")

    await state.clear()  # Очищаем состояние



# Основная функция для запуска бота
async def main():
    # Запуск бота с поллингом
    await dp.start_polling(bot)


if __name__ == "__main__":
    # Запуск программы
    asyncio.run(main())
