from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.callbacks import MenuCallback


def main_menu_keyboard(has_subscription: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_subscription:
        builder.button(text="🔑 Мои ключи", callback_data=MenuCallback(action="keys"))
        builder.button(text="➕ Создать ключ", callback_data=MenuCallback(action="create_key"))
    builder.button(text="💳 Баланс", callback_data=MenuCallback(action="balance"))
    builder.button(text="📖 Инструкция", callback_data=MenuCallback(action="instruction"))
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


def balance_keyboard(monthly_price_rub: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i in range(1, 6):
        amount = monthly_price_rub * i
        builder.button(text=f"Пополнить {amount} ₽ (на {i} мес.)", callback_data=f"topup_{amount}")
    builder.button(text="⬅️ Главное меню", callback_data=MenuCallback(action="main"))
    builder.adjust(1)
    return builder.as_markup()
