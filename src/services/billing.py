from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.integrations.xray.base import XrayGateway, XrayUser, is_bot_managed_email
from src.models.users import User
from src.models.vpn_accesses import VpnAccess, VpnAccessStatus
from src.services.balances import BalanceService


class BillingService:
    def __init__(
        self,
        session: AsyncSession,
        xray_gateway: XrayGateway,
        balance_service: BalanceService,
        subscription_monthly_price_kopecks: int,
    ) -> None:
        self.session = session
        self.xray_gateway = xray_gateway
        self.balance_service = balance_service
        self.subscription_monthly_price_kopecks = subscription_monthly_price_kopecks

    async def try_resume_subscription(self, user: User) -> bool:
        """
        Попытка разблокировать или продлить подписку пользователя при наличии средств.
        Возвращает True, если подписка была успешно продлена/начата.
        """
        now = datetime.now(UTC)
        if user.subscription_expires_at and user.subscription_expires_at > now:
            return False  # Подписка и так активна

        if user.balance_kopecks < self.subscription_monthly_price_kopecks:
            return False  # Недостаточно средств

        # Списываем баланс
        await self.balance_service.charge_balance(
            user=user,
            amount_kopecks=self.subscription_monthly_price_kopecks,
            comment="Автоматическое продление подписки VPN на 30 дней",
        )

        # Продлеваем подписку (если она истекла давно, отсчет идет от сейчас)
        user.subscription_expires_at = now + timedelta(days=30)
        user.notified_about_expiration = False

        # Разблокируем все ключи пользователя
        await self._enable_user_keys(user.id)
        await self.session.flush()
        return True

    async def process_subscriptions(self, bot_send_message_func) -> None:
        """
        Фоновая задача. Ищет юзеров для отправки уведомлений и для отключения/продления.
        bot_send_message_func - функция для отправки сообщения (telegram_id, text).
        """
        now = datetime.now(UTC)
        warning_time = now + timedelta(days=3)

        # 1. Отправка предупреждений (за 3 дня)
        stmt_warn = (
            select(User)
            .where(
                User.subscription_expires_at != None,
                User.subscription_expires_at <= warning_time,
                User.subscription_expires_at > now,
                User.notified_about_expiration == False,
            )
            .with_for_update(skip_locked=True)
        )
        users_to_warn = (await self.session.execute(stmt_warn)).scalars().all()
        for user in users_to_warn:
            user.notified_about_expiration = True
            await self.session.flush()
            try:
                await bot_send_message_func(
                    user.telegram_id,
                    "⚠️ <b>Внимание!</b>\n\nСрок действия вашей подписки на VPN истекает через 3 дня. "
                    "Пожалуйста, пополните баланс, чтобы избежать отключения доступа."
                )
            except Exception:
                pass  # Игнорируем ошибки отправки

        # 2. Обработка просроченных подписок
        stmt_expired = (
            select(User)
            .where(
                User.subscription_expires_at != None,
                User.subscription_expires_at <= now,
            )
            .with_for_update(skip_locked=True)
        )
        expired_users = (await self.session.execute(stmt_expired)).scalars().all()
        for user in expired_users:
            if user.balance_kopecks >= self.subscription_monthly_price_kopecks:
                # Продлеваем
                await self.balance_service.charge_balance(
                    user=user,
                    amount_kopecks=self.subscription_monthly_price_kopecks,
                    comment="Ежемесячная оплата подписки VPN",
                )
                user.subscription_expires_at = now + timedelta(days=30)
                user.notified_about_expiration = False
                await self.session.flush()
                try:
                    await bot_send_message_func(
                        user.telegram_id,
                        "✅ Ваша подписка на VPN была успешно продлена на 30 дней!"
                    )
                except Exception:
                    pass
            else:
                # Отключаем
                # Зануляем дату, чтобы не пытаться списать деньги каждый цикл
                user.subscription_expires_at = None
                user.notified_about_expiration = False
                await self._disable_user_keys(user.id)
                await self.session.flush()
                try:
                    await bot_send_message_func(
                        user.telegram_id,
                        "❌ <b>Подписка истекла</b>\n\n"
                        "На вашем балансе недостаточно средств для продления подписки. "
                        "Доступ к VPN отключен. Пополните баланс, и доступ восстановится автоматически."
                    )
                except Exception:
                    pass

    async def _enable_user_keys(self, user_id: UUID) -> None:
        """Разблокирует все disabled ключи пользователя в БД и Xray."""
        result = await self.session.execute(
            select(VpnAccess).where(
                VpnAccess.user_id == user_id,
                VpnAccess.status == VpnAccessStatus.DISABLED,
            )
        )
        accesses = result.scalars().all()

        for access in accesses:
            access.status = VpnAccessStatus.ACTIVE
            access.last_enabled_at = datetime.now(UTC)
            
            # Возвращаем пользователя в Xray
            if is_bot_managed_email(access.xray_email):
                await self.xray_gateway.add_user(
                    XrayUser(
                        email=access.xray_email,
                        uuid=access.xray_client_uuid,
                        inbound_tag=access.xray_inbound_tag,
                        enabled=True,
                    )
                )

    async def _disable_user_keys(self, user_id: UUID) -> None:
        """Блокирует все активные ключи пользователя в БД и удаляет из Xray."""
        result = await self.session.execute(
            select(VpnAccess).where(
                VpnAccess.user_id == user_id,
                VpnAccess.status == VpnAccessStatus.ACTIVE,
            )
        )
        accesses = result.scalars().all()

        for access in accesses:
            access.status = VpnAccessStatus.DISABLED
            access.last_disabled_at = datetime.now(UTC)
            
            if is_bot_managed_email(access.xray_email):
                await self.xray_gateway.remove_user(
                    access.xray_inbound_tag, access.xray_email
                )
