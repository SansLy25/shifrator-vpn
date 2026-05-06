from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.core.db import async_session_factory
from src.integrations.xray.base import XrayGateway
from src.services.balances import BalanceService
from src.services.users import UserService
from src.services.vpn_accesses import VpnAccessService


class ServiceMiddleware(BaseMiddleware):
    def __init__(self, xray_gateway: XrayGateway, default_inbound_tag: str) -> None:
        self.xray_gateway = xray_gateway
        self.default_inbound_tag = default_inbound_tag

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with async_session_factory() as session:
            data["db_session"] = session
            data["user_service"] = UserService(session)
            data["balance_service"] = BalanceService(session)
            data["vpn_access_service"] = VpnAccessService(
                session=session,
                xray_gateway=self.xray_gateway,
                default_inbound_tag=self.default_inbound_tag,
            )

            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
