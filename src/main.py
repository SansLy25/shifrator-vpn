from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from fastapi import FastAPI

from src.api.health import router as health_router
from src.api.webhooks import router as webhooks_router
from src.bot.setup import create_dispatcher
from src.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.bot = None
    app.state.dispatcher = None

    if settings.bot_token:
        bot = Bot(
            token=settings.bot_token.get_secret_value(),
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        dispatcher = create_dispatcher()

        if settings.telegram_webhook_url:
            await bot.set_webhook(
                url=settings.telegram_webhook_url,
                secret_token=settings.telegram_webhook_secret,
                drop_pending_updates=True,
            )

        app.state.bot = bot
        app.state.dispatcher = dispatcher

    try:
        yield
    finally:
        bot: Bot | None = getattr(app.state, "bot", None)
        if bot is not None:
            await bot.session.close()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
    app.include_router(health_router)
    app.include_router(webhooks_router)
    return app


app = create_app()
