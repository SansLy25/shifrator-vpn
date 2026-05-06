from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base
from src.models.mixins import TimestampMixin


class PaymentProvider(StrEnum):
    TELEGRAM = "telegram"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELED = "canceled"


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False)
    provider: Mapped[PaymentProvider] = mapped_column(
        SAEnum(PaymentProvider, native_enum=False, length=32),
        default=PaymentProvider.TELEGRAM,
        nullable=False,
    )
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, native_enum=False, length=32),
        default=PaymentStatus.PENDING,
        nullable=False,
    )
    amount_kopecks: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB", nullable=False)
    invoice_payload: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    telegram_payment_charge_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    provider_payment_charge_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user = relationship("User", back_populates="payments")
    balance_transactions = relationship("BalanceTransaction", back_populates="payment")
