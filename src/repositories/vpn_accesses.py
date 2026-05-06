from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.vpn_accesses import VpnAccess, VpnAccessStatus


class VpnAccessRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def count_user_keys(self, user_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count(VpnAccess.id)).where(
                VpnAccess.user_id == user_id,
                VpnAccess.status != VpnAccessStatus.DELETED,
            )
        )
        return result.scalar_one()

    async def get_by_id(self, access_id: UUID) -> VpnAccess | None:
        result = await self.session.execute(select(VpnAccess).where(VpnAccess.id == access_id))
        return result.scalar_one_or_none()

    async def get_by_xray_identity(self, inbound_tag: str, email: str) -> VpnAccess | None:
        result = await self.session.execute(
            select(VpnAccess).where(
                VpnAccess.xray_inbound_tag == inbound_tag,
                VpnAccess.xray_email == email,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user_id(self, user_id: UUID) -> list[VpnAccess]:
        result = await self.session.execute(
            select(VpnAccess)
            .where(
                VpnAccess.user_id == user_id,
                VpnAccess.status != VpnAccessStatus.DELETED,
            )
            .order_by(VpnAccess.created_at.asc())
        )
        return list(result.scalars().all())

    def add(self, access: VpnAccess) -> VpnAccess:
        self.session.add(access)
        return access
