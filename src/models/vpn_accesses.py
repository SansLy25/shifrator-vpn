from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base
from src.models.mixins import TimestampMixin


class VpnAccessStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
    EXPIRED = "expired"
    DELETED = "deleted"


class VpnAccess(TimestampMixin, Base):
    __tablename__ = "vpn_accesses"
    __table_args__ = (
        UniqueConstraint("xray_inbound_tag", "xray_email", name="uq_vpn_accesses_xray_identity"),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[VpnAccessStatus] = mapped_column(
        SAEnum(VpnAccessStatus, native_enum=False, length=32),
        default=VpnAccessStatus.ACTIVE,
        nullable=False,
    )
    managed_by: Mapped[str] = mapped_column(String(32), default="bot", nullable=False)
    xray_inbound_tag: Mapped[str] = mapped_column(String(255), nullable=False)
    xray_email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    xray_client_uuid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_enabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    device_limit: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    user = relationship("User", back_populates="vpn_accesses")
