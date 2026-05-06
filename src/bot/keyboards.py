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


def balance_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Пополнить 100 ₽", callback_data="topup_100")
    builder.button(text="Пополнить 500 ₽", callback_data="topup_500")
    builder.button(text="Пополнить 1000 ₽", callback_data="topup_1000")
    builder.button(text="⬅️ Главное меню", callback_data=MenuCallback(action="main"))
    builder.adjust(1)
    return builder.as_markup()
