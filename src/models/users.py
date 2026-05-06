from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base
from src.models.mixins import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    balance_kopecks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_vpn_keys: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    blocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    vpn_accesses = relationship("VpnAccess", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user")
    balance_transactions = relationship("BalanceTransaction", back_populates="user")
