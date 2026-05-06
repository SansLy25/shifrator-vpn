import pytest
from uuid import uuid4

from src.integrations.xray.base import XrayUser
from src.integrations.xray.fake import FakeXrayGateway
from src.models.users import User
from src.services.vpn_accesses import VpnAccessService, VpnKeyLimitExceededError


class MemoryVpnAccessRepository:
    def __init__(self) -> None:
        self.items = []

    async def count_user_keys(self, user_id):
        return len([item for item in self.items if item.user_id == user_id and item.status != "deleted"])

    async def list_by_user_id(self, user_id):
        return [item for item in self.items if item.user_id == user_id]

    def add(self, access):
        self.items.append(access)
        return access


class NoopSession:
    async def flush(self) -> None:
        return None


@pytest.mark.asyncio
async def test_create_key_uses_bot_prefix_and_adds_xray_user(monkeypatch) -> None:
    gateway = FakeXrayGateway()
    service = VpnAccessService(NoopSession(), gateway, default_inbound_tag="vless-reality")
    service.vpn_accesses = MemoryVpnAccessRepository()
    user = User(id=uuid4(), telegram_id=123, max_vpn_keys=10)

    access = await service.create_key(user)

    xray_users = await gateway.list_users("vless-reality")
    assert access.xray_email.startswith("bot:user:123:key:")
    assert xray_users[0].email == access.xray_email


@pytest.mark.asyncio
async def test_create_key_enforces_user_limit() -> None:
    gateway = FakeXrayGateway()
    service = VpnAccessService(NoopSession(), gateway, default_inbound_tag="vless-reality")
    service.vpn_accesses = MemoryVpnAccessRepository()
    user = User(id=uuid4(), telegram_id=123, max_vpn_keys=1)

    await service.create_key(user)

    with pytest.raises(VpnKeyLimitExceededError):
        await service.create_key(user)


@pytest.mark.asyncio
async def test_list_xray_managed_users_ignores_external_users() -> None:
    gateway = FakeXrayGateway()
    await gateway.add_user(XrayUser(email="amnezia@example.com", uuid="external", inbound_tag="vless-reality"))
    await gateway.add_user(XrayUser(email="bot:user:123:key:abc", uuid="bot", inbound_tag="vless-reality"))
    service = VpnAccessService(NoopSession(), gateway, default_inbound_tag="vless-reality")

    users = await service.list_xray_managed_users()

    assert [user.email for user in users] == ["bot:user:123:key:abc"]
