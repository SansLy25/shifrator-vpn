from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.integrations.xray.base import XrayGateway, XrayUser, is_bot_managed_email
from src.models.users import User
from src.models.vpn_accesses import VpnAccess, VpnAccessStatus
from src.repositories.vpn_accesses import VpnAccessRepository


class VpnKeyLimitExceededError(ValueError):
    pass


class VpnAccessNotFoundError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class CreatedVpnAccess:
    id: UUID
    title: str
    xray_email: str
    xray_client_uuid: str
    xray_inbound_tag: str
    expires_at: datetime | None


class VpnAccessService:
    def __init__(
        self,
        session: AsyncSession,
        xray_gateway: XrayGateway,
        default_inbound_tag: str,
    ) -> None:
        self.session = session
        self.xray_gateway = xray_gateway
        self.default_inbound_tag = default_inbound_tag
        self.vpn_accesses = VpnAccessRepository(session)

    async def create_key(
        self,
        user: User,
        title: str | None = None,
        duration_days: int | None = None,
    ) -> CreatedVpnAccess:
        existing_keys_count = await self.vpn_accesses.count_user_keys(user.id)
        if existing_keys_count >= user.max_vpn_keys:
            raise VpnKeyLimitExceededError("User VPN key limit exceeded")

        key_number = existing_keys_count + 1
        client_uuid = str(uuid4())
        xray_email = f"bot:user:{user.telegram_id}:key:{client_uuid}"
        xray_inbound_tag = self.default_inbound_tag
        expires_at = self._build_expires_at(duration_days)

        access = self.vpn_accesses.add(
            VpnAccess(
                user_id=user.id,
                title=title or f"Ключ {key_number}",
                status=VpnAccessStatus.ACTIVE,
                managed_by="bot",
                xray_inbound_tag=xray_inbound_tag,
                xray_email=xray_email,
                xray_client_uuid=client_uuid,
                expires_at=expires_at,
                last_enabled_at=datetime.now(UTC),
            )
        )
        await self.session.flush()

        await self.xray_gateway.add_user(
            XrayUser(
                email=access.xray_email,
                uuid=access.xray_client_uuid,
                inbound_tag=access.xray_inbound_tag,
                enabled=True,
            )
        )

        return CreatedVpnAccess(
            id=access.id,
            title=access.title,
            xray_email=access.xray_email,
            xray_client_uuid=access.xray_client_uuid,
            xray_inbound_tag=access.xray_inbound_tag,
            expires_at=access.expires_at,
        )

    async def revoke_key(self, access_id: UUID) -> None:
        access = await self.vpn_accesses.get_by_id(access_id)
        if access is None:
            raise VpnAccessNotFoundError("VPN access not found")

        if not is_bot_managed_email(access.xray_email):
            return

        access.status = VpnAccessStatus.DELETED
        access.last_disabled_at = datetime.now(UTC)
        await self.session.flush()
        await self.xray_gateway.remove_user(access.xray_inbound_tag, access.xray_email)

    async def list_user_keys(self, user: User) -> list[VpnAccess]:
        return await self.vpn_accesses.list_by_user_id(user.id)

    async def list_xray_managed_users(self) -> list[XrayUser]:
        users = await self.xray_gateway.list_users(self.default_inbound_tag)
        return [user for user in users if is_bot_managed_email(user.email)]

    @staticmethod
    def _build_expires_at(duration_days: int | None) -> datetime | None:
        if duration_days is None:
            return None
        if duration_days <= 0:
            raise ValueError("Duration must be positive")
        return datetime.now(UTC) + timedelta(days=duration_days)
