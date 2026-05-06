from src.integrations.xray.base import XrayGateway, XrayUser


class XrayGrpcGateway(XrayGateway):
    def __init__(self, api_address: str) -> None:
        self.api_address = api_address

    async def list_users(self, inbound_tag: str) -> list[XrayUser]:
        raise NotImplementedError("Xray gRPC integration will be added after API config is confirmed.")

    async def add_user(self, user: XrayUser) -> None:
        raise NotImplementedError("Xray gRPC integration will be added after API config is confirmed.")

    async def remove_user(self, inbound_tag: str, email: str) -> None:
        raise NotImplementedError("Xray gRPC integration will be added after API config is confirmed.")
