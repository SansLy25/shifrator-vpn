from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.db import async_session_factory
from src.integrations.xray.base import XrayGateway
from src.services.balances import BalanceService
from src.services.subscriptions import SubscriptionService
from src.services.users import UserService
from src.services.vpn_accesses import VpnAccessService


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_xray_gateway(request: Request) -> XrayGateway:
    return request.app.state.xray_gateway


def get_user_service(session: AsyncSession = Depends(get_db_session)) -> UserService:
    return UserService(session)


def get_balance_service(session: AsyncSession = Depends(get_db_session)) -> BalanceService:
    return BalanceService(session)


def get_vpn_access_service(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    balance_service: BalanceService = Depends(get_balance_service),
) -> VpnAccessService:
    return VpnAccessService(
        session=session,
        xray_gateway=request.app.state.xray_gateway,
        default_inbound_tag=settings.xray_default_inbound_tag,
        balance_service=balance_service,
        subscription_monthly_price_kopecks=settings.vpn_subscription_monthly_rub * 100,
    )


def get_subscription_service(request: Request) -> SubscriptionService:
    return request.app.state.subscription_service
