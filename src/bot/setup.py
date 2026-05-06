from aiogram import Dispatcher

from src.bot.handlers import router as main_router


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(main_router)
    return dispatcher
