from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.users import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id) -> User | None:
        return await self.session.get(User, user_id)

    def add(self, user: User) -> User:
        self.session.add(user)
        return user
