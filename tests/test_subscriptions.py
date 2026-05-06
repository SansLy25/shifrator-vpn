import pytest

from src.integrations.xray.base import XrayUser
from src.integrations.xray.fake import FakeXrayGateway
from src.services.subscriptions import SubscriptionService


@pytest.mark.asyncio
async def test_issue_access_creates_only_bot_managed_user() -> None:
    gateway = FakeXrayGateway()
    service = SubscriptionService(gateway, default_inbound_tag="vless-reality")

    access = await service.issue_access(telegram_id=123)

    users = await gateway.list_users("vless-reality")
    assert len(users) == 1
    assert users[0].email == "bot:telegram:123"
    assert users[0].uuid == access.uuid


@pytest.mark.asyncio
async def test_list_managed_users_ignores_external_amnezia_users() -> None:
    gateway = FakeXrayGateway()
    await gateway.add_user(
        XrayUser(
            email="amnezia-user@example.com",
            uuid="external",
            inbound_tag="vless-reality",
        )
    )
    service = SubscriptionService(gateway, default_inbound_tag="vless-reality")

    await service.issue_access(telegram_id=123)

    managed_users = await service.list_managed_users()
    assert [user.email for user in managed_users] == ["bot:telegram:123"]
