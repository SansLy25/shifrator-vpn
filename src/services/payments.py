import secrets
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.payments import Payment, PaymentProvider, PaymentStatus
from src.models.users import User
from src.repositories.payments import PaymentRepository
from src.services.balances import BalanceService
from src.services.billing import BillingService


class PaymentNotFoundError(ValueError):
    pass


class PaymentAlreadyProcessedError(ValueError):
    pass


class PaymentService:
    def __init__(self, session: AsyncSession, balance_service: BalanceService, billing_service: BillingService) -> None:
        self.session = session
        self.balance_service = balance_service
        self.billing_service = billing_service
        self.payments = PaymentRepository(session)

    async def create_payment(self, user: User, amount_kopecks: int, currency: str = "RUB") -> Payment:
        if amount_kopecks <= 0:
            raise ValueError("Payment amount must be positive")

        invoice_payload = secrets.token_urlsafe(32)
        payment = Payment(
            user_id=user.id,
            provider=PaymentProvider.TELEGRAM,
            status=PaymentStatus.PENDING,
            amount_kopecks=amount_kopecks,
            currency=currency,
            invoice_payload=invoice_payload,
        )
        self.payments.add(payment)
        await self.session.flush()
        return payment

    async def complete_payment(
        self,
        invoice_payload: str,
        telegram_payment_charge_id: str,
        provider_payment_charge_id: str,
    ) -> Payment:
        payment = await self.payments.get_by_invoice_payload(invoice_payload)
        if not payment:
            raise PaymentNotFoundError("Payment with given invoice payload not found")

        if payment.status == PaymentStatus.SUCCEEDED:
            # Idempotency: if already processed, just return it
            return payment
        elif payment.status != PaymentStatus.PENDING:
            raise PaymentAlreadyProcessedError(f"Payment is in {payment.status} state")

        payment.status = PaymentStatus.SUCCEEDED
        payment.telegram_payment_charge_id = telegram_payment_charge_id
        payment.provider_payment_charge_id = provider_payment_charge_id
        payment.paid_at = datetime.now(timezone.utc)

        # Since we need to mutate User's balance, we must lock it or just fetch it.
        from src.repositories.users import UserRepository
        user_repo = UserRepository(self.session)
        user = await user_repo.get_by_id(payment.user_id)
        if not user:
            raise ValueError("User associated with payment not found")

        await self.balance_service.add_balance(
            user=user,
            amount_kopecks=payment.amount_kopecks,
            comment=f"Пополнение через Telegram (ID: {telegram_payment_charge_id})",
        )
        
        # Пытаемся разблокировать или продлить подписку
        # (Баланс только что пополнен, поэтому если его хватает, подписка продлится)
        await self.billing_service.try_resume_subscription(user)
        
        await self.session.flush()
        return payment

    async def fail_payment(self, invoice_payload: str) -> Payment:
        payment = await self.payments.get_by_invoice_payload(invoice_payload)
        if not payment:
            raise PaymentNotFoundError("Payment with given invoice payload not found")

        if payment.status == PaymentStatus.PENDING:
            payment.status = PaymentStatus.FAILED
            await self.session.flush()
            
        return payment
