import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.core.configurate import BOT_TOKEN

logging.basicConfig(level=logging.INFO)
# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Определение состояния
class FindArtikul(StatesGroup):
    choosing_artikul = State()


# Клавиатура для стартового сообщения
def get_keyboard_start():
    buttons = [
        [InlineKeyboardButton(text='Получить данные по товару', callback_data='get_artikul')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Хендлер для команды /start
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Здравствуйте, для продолжения используйте кнопку.", reply_markup=get_keyboard_start())


# Хендлер для кнопки "Получить данные по товару"
@dp.callback_query(F.data == 'get_artikul')
async def get_art(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Пришлите артикул.")
    await callback.answer()
    await state.set_state(FindArtikul.choosing_artikul)


# Хендлер для получения артикула
@dp.message(FindArtikul.choosing_artikul)
async def get_product_data(message: types.Message, state: FSMContext):
    # Здесь можно добавить логику для получения данных из API
    await message.answer(
        f"Название товара: {'Товар пример'}\n"
        f"Артикул: {message.text}\n"
        f"Цена: {112233}\n"
        f"Рейтинг товара: {3.5}\n"
        f"Количество товара: {555}"
    )
    await state.clear()


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())