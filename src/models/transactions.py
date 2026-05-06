from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base
from src.models.mixins import TimestampMixin


class BalanceTransactionType(StrEnum):
    PAYMENT = "payment"
    SUBSCRIPTION_CHARGE = "subscription_charge"
    REFUND = "refund"
    MANUAL_ADJUSTMENT = "manual_adjustment"


class BalanceTransaction(TimestampMixin, Base):
    __tablename__ = "balance_transactions"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False)
    payment_id: Mapped[UUID | None] = mapped_column(ForeignKey("payments.id", ondelete="SET NULL"), index=True)
    type: Mapped[BalanceTransactionType] = mapped_column(
        SAEnum(BalanceTransactionType, native_enum=False, length=32),
        nullable=False,
    )
    amount_kopecks: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after_kopecks: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(String(500))

    user = relationship("User", back_populates="balance_transactions")
    payment = relationship("Payment", back_populates="balance_transactions")
