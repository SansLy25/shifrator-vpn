from sqlalchemy.ext.asyncio import AsyncSession

from src.models.transactions import BalanceTransaction


class BalanceTransactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, transaction: BalanceTransaction) -> BalanceTransaction:
        self.session.add(transaction)
        return transaction
