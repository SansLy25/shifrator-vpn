from dataclasses import dataclass
from uuid import uuid4

from src.integrations.xray.base import (
    XrayGateway,
    XrayUser,
    build_bot_user_email,
    is_bot_managed_email,
)


@dataclass(frozen=True, slots=True)
class VpnAccess:
    telegram_id: int
    email: str
    uuid: str
    inbound_tag: str


class SubscriptionService:
    def __init__(self, xray_gateway: XrayGateway, default_inbound_tag: str) -> None:
        self.xray_gateway = xray_gateway
        self.default_inbound_tag = default_inbound_tag

    async def issue_access(self, telegram_id: int) -> VpnAccess:
        email = build_bot_user_email(telegram_id)
        existing_user = await self._find_bot_user(email)

        if existing_user is None:
            user = XrayUser(
                email=email,
                uuid=str(uuid4()),
                inbound_tag=self.default_inbound_tag,
                enabled=True,
            )
            await self.xray_gateway.add_user(user)
        else:
            user = existing_user

        return VpnAccess(
            telegram_id=telegram_id,
            email=user.email,
            uuid=user.uuid,
            inbound_tag=user.inbound_tag,
        )

    async def revoke_access(self, telegram_id: int) -> None:
        email = build_bot_user_email(telegram_id)
        if not is_bot_managed_email(email):
            return

        await self.xray_gateway.remove_user(self.default_inbound_tag, email)

    async def list_managed_users(self) -> list[XrayUser]:
        users = await self.xray_gateway.list_users(self.default_inbound_tag)
        return [user for user in users if is_bot_managed_email(user.email)]

    async def _find_bot_user(self, email: str) -> XrayUser | None:
        users = await self.xray_gateway.list_users(self.default_inbound_tag)
        for user in users:
            if user.email == email and is_bot_managed_email(user.email):
                return user
        return None
