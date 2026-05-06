from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.users import User
from src.services.balances import BalanceService
from src.services.billing import BillingService


class MockBalanceService:
    async def add_balance(self, user: User, amount_kopecks: int, comment: str) -> None:
        user.balance_kopecks += amount_kopecks


class MockXrayGateway:
    async def add_user(self, user):
        pass

    async def remove_user(self, inbound_tag, email):
        pass


class NoopSession:
    async def flush(self) -> None:
        pass


@pytest.fixture
def user():
    return User(
        id=uuid4(),
        telegram_id=123,
        balance_kopecks=0,
        subscription_expires_at=None,
    )


@pytest.fixture
def billing_service():
    return BillingService(
        session=NoopSession(),  # type: ignore
        xray_gateway=MockXrayGateway(),  # type: ignore
        balance_service=MockBalanceService(),  # type: ignore
        subscription_monthly_price_kopecks=15000,
    )


@pytest.mark.asyncio
async def test_try_resume_subscription_active(billing_service: BillingService, user: User):
    user.subscription_expires_at = datetime.now(UTC) + timedelta(days=10)
    result = await billing_service.try_resume_subscription(user)
    assert result is False


@pytest.mark.asyncio
async def test_try_resume_subscription_insufficient_funds(billing_service: BillingService, user: User):
    user.subscription_expires_at = datetime.now(UTC) - timedelta(days=1)
    user.balance_kopecks = 5000  # less than 15000
    result = await billing_service.try_resume_subscription(user)
    assert result is False


@pytest.mark.asyncio
async def test_try_resume_subscription_success(billing_service: BillingService, user: User, monkeypatch):
    user.subscription_expires_at = datetime.now(UTC) - timedelta(days=1)
    user.balance_kopecks = 20000

    # Mock _enable_user_keys since it uses DB queries
    enable_keys_mock = AsyncMock()
    monkeypatch.setattr(billing_service, "_enable_user_keys", enable_keys_mock)

    result = await billing_service.try_resume_subscription(user)
    
    assert result is True
    assert user.balance_kopecks == 5000  # 20000 - 15000
    assert user.subscription_expires_at > datetime.now(UTC) + timedelta(days=29)
    assert user.notified_about_expiration is False
    enable_keys_mock.assert_called_once_with(user.id)
