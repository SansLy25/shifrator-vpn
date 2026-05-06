from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.payments import Payment


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_invoice_payload(self, invoice_payload: str) -> Payment | None:
        result = await self.session.execute(select(Payment).where(Payment.invoice_payload == invoice_payload))
        return result.scalar_one_or_none()

    async def get_by_telegram_charge_id(self, charge_id: str) -> Payment | None:
        result = await self.session.execute(
            select(Payment).where(Payment.telegram_payment_charge_id == charge_id)
        )
        return result.scalar_one_or_none()

    def add(self, payment: Payment) -> Payment:
        self.session.add(payment)
        return payment
