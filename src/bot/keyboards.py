from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.callbacks import MenuCallback


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔑 Мои ключи", callback_data=MenuCallback(action="keys"))
    builder.button(text="💳 Баланс", callback_data=MenuCallback(action="balance"))
    builder.button(text="➕ Создать ключ", callback_data=MenuCallback(action="create_key"))
    builder.adjust(1)
    return builder.as_markup()


def keys_menu_keyboard(can_create_key: bool = True) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if can_create_key:
        builder.button(text="➕ Создать ключ", callback_data=MenuCallback(action="create_key"))
    builder.button(text="⬅️ Главное меню", callback_data=MenuCallback(action="main"))
    builder.adjust(1)
    return builder.as_markup()


def back_to_main_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Главное меню", callback_data=MenuCallback(action="main"))
    return builder.as_markup()
