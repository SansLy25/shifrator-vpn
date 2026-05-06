from aiogram import Dispatcher

from src.bot.handlers import router as main_router
from src.bot.middlewares import ServiceMiddleware
from src.integrations.xray.base import XrayGateway


def create_dispatcher(xray_gateway: XrayGateway, default_inbound_tag: str) -> Dispatcher:
    dispatcher = Dispatcher()
    service_middleware = ServiceMiddleware(
        xray_gateway=xray_gateway,
        default_inbound_tag=default_inbound_tag,
    )
    dispatcher.message.middleware(service_middleware)
    dispatcher.callback_query.middleware(service_middleware)
    dispatcher.include_router(main_router)
    return dispatcher
