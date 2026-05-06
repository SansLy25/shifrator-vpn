from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router(name="main")


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer(
        "Привет. Я бот для управления VPN-доступом.\n\n"
        "Каркас запущен: webhook принимает обновления Telegram."
    )


@router.message()
async def handle_unknown_message(message: Message) -> None:
    await message.answer("Команда пока не реализована. Доступна команда /start.")
