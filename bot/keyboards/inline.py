from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
# Клавиатура для стартового сообщения
def get_keyboard_start():
    buttons = [
        [InlineKeyboardButton(text='Получить данные по товару', callback_data='get_artikul')],
        [InlineKeyboardButton(text='Добавить товар в базу (Админ)', callback_data='add_product')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def create_subscribe_button(artikul: int):
    buttons = [
        [InlineKeyboardButton(text="Подписаться на обновления", callback_data=f"subscribe_{artikul}")],
        [InlineKeyboardButton(text='Добавить товар в базу (Админ)', callback_data='add_product')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
