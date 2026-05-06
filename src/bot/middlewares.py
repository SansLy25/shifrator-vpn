from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.core.config import settings
from src.core.db import async_session_factory
from src.integrations.xray.base import XrayGateway
from src.integrations.xray.link_builder import VpnLinkBuilder
from src.services.balances import BalanceService
from src.services.billing import BillingService
from src.services.payments import PaymentService
from src.services.users import UserService
from src.services.vpn_accesses import VpnAccessService


class ServiceMiddleware(BaseMiddleware):
    def __init__(
        self, xray_gateway: XrayGateway, default_inbound_tag: str, vpn_link_builder: VpnLinkBuilder
    ) -> None:
        self.xray_gateway = xray_gateway
        self.default_inbound_tag = default_inbound_tag
        self.vpn_link_builder = vpn_link_builder

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with async_session_factory() as session:
            data["db_session"] = session
            data["user_service"] = UserService(session)
            balance_service = BalanceService(session)
            data["balance_service"] = balance_service
            billing_service = BillingService(
                session=session,
                xray_gateway=self.xray_gateway,
                balance_service=balance_service,
                subscription_monthly_price_kopecks=settings.vpn_subscription_monthly_rub * 100,
            )
            data["billing_service"] = billing_service
            data["payment_service"] = PaymentService(session, balance_service, billing_service)
            data["vpn_access_service"] = VpnAccessService(
                session=session,
                xray_gateway=self.xray_gateway,
                default_inbound_tag=self.default_inbound_tag,
                balance_service=balance_service,
                subscription_monthly_price_kopecks=settings.vpn_subscription_monthly_rub * 100,
            )
            data["vpn_link_builder"] = self.vpn_link_builder

            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
