from sqlalchemy.ext.asyncio import AsyncSession

from src.models.transactions import BalanceTransaction, BalanceTransactionType
from src.models.users import User
from src.repositories.transactions import BalanceTransactionRepository


class InsufficientBalanceError(ValueError):
    pass


class BalanceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.transactions = BalanceTransactionRepository(session)

    async def add_balance(
        self,
        user: User,
        amount_kopecks: int,
        transaction_type: BalanceTransactionType = BalanceTransactionType.PAYMENT,
        comment: str | None = None,
    ) -> BalanceTransaction:
        if amount_kopecks <= 0:
            raise ValueError("Balance top-up amount must be positive")

        user.balance_kopecks += amount_kopecks
        transaction = self.transactions.add(
            BalanceTransaction(
                user_id=user.id,
                type=transaction_type,
                amount_kopecks=amount_kopecks,
                balance_after_kopecks=user.balance_kopecks,
                comment=comment,
            )
        )
        await self.session.flush()
        return transaction

    async def charge_balance(
        self,
        user: User,
        amount_kopecks: int,
        comment: str | None = None,
    ) -> BalanceTransaction:
        if amount_kopecks <= 0:
            raise ValueError("Charge amount must be positive")
        if user.balance_kopecks < amount_kopecks:
            raise InsufficientBalanceError("User has insufficient balance")

        user.balance_kopecks -= amount_kopecks
        transaction = self.transactions.add(
            BalanceTransaction(
                user_id=user.id,
                type=BalanceTransactionType.SUBSCRIPTION_CHARGE,
                amount_kopecks=-amount_kopecks,
                balance_after_kopecks=user.balance_kopecks,
                comment=comment,
            )
        )
        await self.session.flush()
        return transaction
