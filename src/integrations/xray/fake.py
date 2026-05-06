from src.integrations.xray.base import XrayGateway, XrayUser


class FakeXrayGateway(XrayGateway):
    def __init__(self) -> None:
        self._users_by_inbound: dict[str, dict[str, XrayUser]] = {}

    async def list_users(self, inbound_tag: str) -> list[XrayUser]:
        users = self._users_by_inbound.get(inbound_tag, {})
        return list(users.values())

    async def add_user(self, user: XrayUser) -> None:
        users = self._users_by_inbound.setdefault(user.inbound_tag, {})
        users[user.email] = user

    async def remove_user(self, inbound_tag: str, email: str) -> None:
        users = self._users_by_inbound.setdefault(inbound_tag, {})
        users.pop(email, None)
