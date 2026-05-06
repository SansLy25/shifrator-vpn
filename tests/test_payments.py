import pytest

from src.models.payments import Payment, PaymentStatus
from src.models.users import User
from src.services.balances import BalanceService
from src.services.payments import PaymentAlreadyProcessedError, PaymentNotFoundError, PaymentService


class MemoryPaymentRepository:
    def __init__(self):
        self.items = []

    async def get_by_invoice_payload(self, invoice_payload: str) -> Payment | None:
        return next((p for p in self.items if p.invoice_payload == invoice_payload), None)

    def add(self, payment: Payment) -> Payment:
        self.items.append(payment)
        return payment


class MemoryTransactionRepository:
    def add(self, t):
        return t


class MemoryUserRepository:
    def __init__(self, user):
        self.user = user

    async def get_by_id(self, user_id):
        return self.user


class NoopSession:
    async def flush(self) -> None:
        pass


@pytest.fixture
def user():
    return User(id="test-uuid", telegram_id=123, balance_kopecks=0)


@pytest.fixture
def balance_service():
    service = BalanceService(NoopSession())
    service.transactions = MemoryTransactionRepository()
    return service


class MockBillingService:
    async def try_resume_subscription(self, user: User) -> bool:
        return False


@pytest.fixture
def payment_service(balance_service, user, monkeypatch):
    billing_service = MockBillingService()
    service = PaymentService(NoopSession(), balance_service, billing_service)
    service.payments = MemoryPaymentRepository()
    
    monkeypatch.setattr("src.repositories.users.UserRepository", lambda session: MemoryUserRepository(user))
    
    return service


@pytest.mark.asyncio
async def test_create_payment(payment_service: PaymentService, user: User):
    payment = await payment_service.create_payment(user, 50000)
    
    assert payment.user_id == user.id
    assert payment.amount_kopecks == 50000
    assert payment.status == PaymentStatus.PENDING
    assert payment.invoice_payload is not None


@pytest.mark.asyncio
async def test_complete_payment(payment_service: PaymentService, user: User):
    payment = await payment_service.create_payment(user, 50000)
    assert user.balance_kopecks == 0

    completed_payment = await payment_service.complete_payment(
        invoice_payload=payment.invoice_payload,
        telegram_payment_charge_id="test_tg_charge",
        provider_payment_charge_id="test_provider_charge",
    )

    assert completed_payment.status == PaymentStatus.SUCCEEDED
    assert completed_payment.telegram_payment_charge_id == "test_tg_charge"
    assert user.balance_kopecks == 50000


@pytest.mark.asyncio
async def test_complete_payment_idempotency(payment_service: PaymentService, user: User):
    payment = await payment_service.create_payment(user, 50000)
    
    await payment_service.complete_payment(
        invoice_payload=payment.invoice_payload,
        telegram_payment_charge_id="test_tg_charge",
        provider_payment_charge_id="test_provider_charge",
    )

    await payment_service.complete_payment(
        invoice_payload=payment.invoice_payload,
        telegram_payment_charge_id="test_tg_charge",
        provider_payment_charge_id="test_provider_charge",
    )

    assert user.balance_kopecks == 50000


@pytest.mark.asyncio
async def test_complete_payment_not_found(payment_service: PaymentService):
    with pytest.raises(PaymentNotFoundError):
        await payment_service.complete_payment(
            invoice_payload="invalid_payload",
            telegram_payment_charge_id="test",
            provider_payment_charge_id="test",
        )

