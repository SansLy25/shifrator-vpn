import asyncio
import logging
from typing import Callable, Coroutine

from sqlalchemy.ext.asyncio import async_sessionmaker

from src.core.config import settings
from src.integrations.xray.base import XrayGateway
from src.services.balances import BalanceService
from src.services.billing import BillingService

logger = logging.getLogger(__name__)


async def billing_worker(
    session_factory: async_sessionmaker,
    xray_gateway: XrayGateway,
    bot_send_message_func: Callable[[int, str], Coroutine],
) -> None:
    """
    Фоновый воркер для проверки и обработки подписок.
    Просыпается каждый час (или чаще для теста).
    """
    logger.info("Billing worker started.")
    while True:
        try:
            async with session_factory() as session:
                balance_service = BalanceService(session)
                billing_service = BillingService(
                    session=session,
                    xray_gateway=xray_gateway,
                    balance_service=balance_service,
                    subscription_monthly_price_kopecks=settings.vpn_subscription_monthly_rub * 100,
                )
                await billing_service.process_subscriptions(bot_send_message_func)
                await session.commit()
        except asyncio.CancelledError:
            logger.info("Billing worker cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in billing worker: {e}", exc_info=True)
            # В случае ошибки session будет откачен (или закрыт), мы просто продолжим после паузы

        # Запускаем раз в 1 час
        # Для тестирования можно сделать раз в минуту, но в продакшене лучше раз в час
        await asyncio.sleep(3600)
