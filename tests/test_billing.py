from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, call
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.users import User
from src.models.vpn_accesses import VpnAccess, VpnAccessStatus
from src.services.balances import BalanceService
from src.services.billing import BillingService


class MockBalanceService:
    async def add_balance(self, user: User, amount_kopecks: int, comment: str) -> None:
        user.balance_kopecks += amount_kopecks
        
    async def charge_balance(self, user: User, amount_kopecks: int, comment: str) -> None:
        user.balance_kopecks -= amount_kopecks


class MockXrayGateway:
    def __init__(self):
        self.add_user = AsyncMock()
        self.remove_user = AsyncMock()


class MockResult:
    def __init__(self, data):
        self.data = data
        
    def scalars(self):
        class MockScalars:
            def all(inner_self):
                return self.data
        return MockScalars()


class MockSession:
    def __init__(self):
        self.execute = AsyncMock()
        self.flush = AsyncMock()


@pytest.fixture
def user():
    return User(
        id=uuid4(),
        telegram_id=123,
        balance_kopecks=0,
        subscription_expires_at=None,
    )


@pytest.fixture
def session_mock():
    return MockSession()


@pytest.fixture
def xray_gateway():
    return MockXrayGateway()


@pytest.fixture
def billing_service(session_mock, xray_gateway):
    return BillingService(
        session=session_mock,  # type: ignore
        xray_gateway=xray_gateway,  # type: ignore
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


@pytest.mark.asyncio
async def test_enable_user_keys(billing_service: BillingService, session_mock: MockSession, xray_gateway: MockXrayGateway):
    user_id = uuid4()
    access1 = VpnAccess(
        id=uuid4(),
        user_id=user_id,
        status=VpnAccessStatus.DISABLED,
        xray_email=f"bot:user:123:key:uuid1",
        xray_client_uuid="uuid1",
        xray_inbound_tag="vless-reality"
    )
    access2 = VpnAccess(
        id=uuid4(),
        user_id=user_id,
        status=VpnAccessStatus.DISABLED,
        xray_email="manual-email",  # Not a bot-managed email
        xray_client_uuid="uuid2",
        xray_inbound_tag="vless-reality"
    )
    
    session_mock.execute.return_value = MockResult([access1, access2])
    
    await billing_service._enable_user_keys(user_id)
    
    # Check status changes
    assert access1.status == VpnAccessStatus.ACTIVE
    assert access1.last_enabled_at is not None
    assert access2.status == VpnAccessStatus.ACTIVE
    assert access2.last_enabled_at is not None
    
    # Check Xray interactions (only bot-managed emails should be sent)
    xray_gateway.add_user.assert_called_once()
    called_user = xray_gateway.add_user.call_args[0][0]
    assert called_user.email == access1.xray_email
    assert called_user.uuid == access1.xray_client_uuid
    assert called_user.enabled is True


@pytest.mark.asyncio
async def test_disable_user_keys(billing_service: BillingService, session_mock: MockSession, xray_gateway: MockXrayGateway):
    user_id = uuid4()
    access1 = VpnAccess(
        id=uuid4(),
        user_id=user_id,
        status=VpnAccessStatus.ACTIVE,
        xray_email=f"bot:user:123:key:uuid1",
        xray_client_uuid="uuid1",
        xray_inbound_tag="vless-reality"
    )
    
    session_mock.execute.return_value = MockResult([access1])
    
    await billing_service._disable_user_keys(user_id)
    
    assert access1.status == VpnAccessStatus.DISABLED
    assert access1.last_disabled_at is not None
    
    xray_gateway.remove_user.assert_called_once_with("vless-reality", access1.xray_email)


@pytest.mark.asyncio
async def test_process_subscriptions_warns_users(billing_service: BillingService, session_mock: MockSession):
    user = User(
        id=uuid4(),
        telegram_id=12345,
        balance_kopecks=0,
        subscription_expires_at=datetime.now(UTC) + timedelta(days=2),
        notified_about_expiration=False
    )
    
    # We have 2 DB queries in process_subscriptions: 1 for warnings, 1 for expirations.
    # We will mock session.execute to return the user on the first call, and empty on the second.
    session_mock.execute.side_effect = [
        MockResult([user]),
        MockResult([])
    ]
    
    bot_send_message_mock = AsyncMock()
    
    await billing_service.process_subscriptions(bot_send_message_mock)
    
    assert user.notified_about_expiration is True
    bot_send_message_mock.assert_called_once()
    assert bot_send_message_mock.call_args[0][0] == 12345
    assert "через 3 дня" in bot_send_message_mock.call_args[0][1]


@pytest.mark.asyncio
async def test_process_subscriptions_expires_users(billing_service: BillingService, session_mock: MockSession, monkeypatch):
    user_expired_no_money = User(
        id=uuid4(),
        telegram_id=111,
        balance_kopecks=5000, # Not enough
        subscription_expires_at=datetime.now(UTC) - timedelta(days=1),
        notified_about_expiration=True
    )
    user_expired_with_money = User(
        id=uuid4(),
        telegram_id=222,
        balance_kopecks=20000, # Enough
        subscription_expires_at=datetime.now(UTC) - timedelta(days=1),
        notified_about_expiration=True
    )
    
    session_mock.execute.side_effect = [
        MockResult([]), # No warnings
        MockResult([user_expired_no_money, user_expired_with_money]) # Expirations
    ]
    
    bot_send_message_mock = AsyncMock()
    disable_keys_mock = AsyncMock()
    monkeypatch.setattr(billing_service, "_disable_user_keys", disable_keys_mock)
    
    await billing_service.process_subscriptions(bot_send_message_mock)
    
    # Check no money user
    assert user_expired_no_money.subscription_expires_at is None
    assert user_expired_no_money.balance_kopecks == 5000
    disable_keys_mock.assert_called_once_with(user_expired_no_money.id)
    
    # Check with money user
    assert user_expired_with_money.subscription_expires_at > datetime.now(UTC) + timedelta(days=29)
    assert user_expired_with_money.balance_kopecks == 5000 # 20000 - 15000
    assert user_expired_with_money.notified_about_expiration is False
    
    # Check messages sent
    assert bot_send_message_mock.call_count == 2
    calls = bot_send_message_mock.call_args_list
    
    # Verify exact messages
    msg1 = next(c for c in calls if c[0][0] == 111)
    assert "отключен" in msg1[0][1]
    
    msg2 = next(c for c in calls if c[0][0] == 222)
    assert "успешно продлена" in msg2[0][1]
