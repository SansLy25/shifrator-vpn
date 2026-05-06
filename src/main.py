import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from fastapi import FastAPI

from src.api.dev import router as dev_router
from src.api.health import router as health_router
from src.api.webhooks import router as webhooks_router
from src.bot.setup import create_dispatcher
from src.bot.tasks import billing_worker
from src.core.config import settings
from src.core.db import async_session_factory
from src.integrations.xray.fake import FakeXrayGateway
from src.integrations.xray.grpc import XrayGrpcGateway
from src.integrations.xray.link_builder import VpnLinkBuilder
from src.services.subscriptions import SubscriptionService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.bot = None
    app.state.dispatcher = None
    app.state.xray_gateway = create_xray_gateway()
    app.state.vpn_link_builder = create_vpn_link_builder()
    app.state.subscription_service = SubscriptionService(
        xray_gateway=app.state.xray_gateway,
        default_inbound_tag=settings.xray_default_inbound_tag,
    )

    if settings.bot_token:
        bot = Bot(
            token=settings.bot_token.get_secret_value(),
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        dispatcher = create_dispatcher(
            xray_gateway=app.state.xray_gateway,
            default_inbound_tag=settings.xray_default_inbound_tag,
            vpn_link_builder=app.state.vpn_link_builder,
        )

        if settings.telegram_webhook_url:
            await bot.set_webhook(
                url=settings.telegram_webhook_url,
                secret_token=settings.telegram_webhook_secret,
                drop_pending_updates=True,
                allowed_updates=dispatcher.resolve_used_update_types(),
            )

        app.state.bot = bot
        app.state.dispatcher = dispatcher

        app.state.billing_task = asyncio.create_task(
            billing_worker(
                session_factory=async_session_factory,
                xray_gateway=app.state.xray_gateway,
                bot_send_message_func=bot.send_message,
            )
        )

    try:
        yield
    finally:
        billing_task = getattr(app.state, "billing_task", None)
        if billing_task is not None:
            billing_task.cancel()

        bot: Bot | None = getattr(app.state, "bot", None)
        if bot is not None:
            await bot.session.close()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
    app.include_router(health_router)
    if settings.debug:
        app.include_router(dev_router)
    app.include_router(webhooks_router)
    return app


def create_xray_gateway() -> FakeXrayGateway | XrayGrpcGateway:
    if settings.xray_gateway == "fake":
        return FakeXrayGateway()
    if settings.xray_gateway == "grpc":
        return XrayGrpcGateway(settings.xray_api_address)
    raise ValueError(f"Unsupported Xray gateway: {settings.xray_gateway}")


def create_vpn_link_builder() -> VpnLinkBuilder:
    return VpnLinkBuilder(
        host=settings.xray_host,
        port=settings.xray_port,
        public_key=settings.xray_public_key,
        short_id=settings.xray_short_id,
        sni=settings.xray_sni,
        flow=settings.xray_flow,
    )


app = create_app()
