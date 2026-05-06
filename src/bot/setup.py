from aiogram import Dispatcher

from src.bot.handlers import router as main_router
from src.bot.handlers_payments import router as payments_router
from src.bot.middlewares import ServiceMiddleware
from src.integrations.xray.base import XrayGateway
from src.integrations.xray.link_builder import VpnLinkBuilder


def create_dispatcher(
    xray_gateway: XrayGateway, default_inbound_tag: str, vpn_link_builder: VpnLinkBuilder
) -> Dispatcher:
    dispatcher = Dispatcher()
    service_middleware = ServiceMiddleware(
        xray_gateway=xray_gateway,
        default_inbound_tag=default_inbound_tag,
        vpn_link_builder=vpn_link_builder,
    )
    dispatcher.message.middleware(service_middleware)
    dispatcher.callback_query.middleware(service_middleware)
    dispatcher.pre_checkout_query.middleware(service_middleware)
    dispatcher.include_router(payments_router)
    dispatcher.include_router(main_router)
    return dispatcher
