from dataclasses import dataclass
from typing import Protocol


BOT_USER_EMAIL_PREFIX = "bot:"


@dataclass(frozen=True, slots=True)
class XrayUser:
    email: str
    uuid: str
    inbound_tag: str
    enabled: bool = True


class XrayGateway(Protocol):
    async def list_users(self, inbound_tag: str) -> list[XrayUser]:
        raise NotImplementedError

    async def add_user(self, user: XrayUser) -> None:
        raise NotImplementedError

    async def remove_user(self, inbound_tag: str, email: str) -> None:
        raise NotImplementedError


def build_bot_user_email(telegram_id: int) -> str:
    return f"{BOT_USER_EMAIL_PREFIX}telegram:{telegram_id}"


def is_bot_managed_email(email: str) -> bool:
    return email.startswith(BOT_USER_EMAIL_PREFIX)
