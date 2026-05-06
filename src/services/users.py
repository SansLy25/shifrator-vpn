from sqlalchemy.ext.asyncio import AsyncSession

from src.models.users import User
from src.repositories.users import UserRepository


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def get_or_create_from_telegram(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> User:
        user = await self.users.get_by_telegram_id(telegram_id)
        if user is None:
            user = self.users.add(
                User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                )
            )
            await self.session.flush()
            return user

        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        await self.session.flush()
        return user
