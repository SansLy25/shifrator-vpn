import grpc
from google.protobuf.any_pb2 import Any

from src.integrations.xray.base import XrayGateway, XrayUser
from src.integrations.xray.generated.account_vless_pb2 import Account as VlessAccount
from src.integrations.xray.generated.command_pb2 import (
    AddUserOperation,
    AlterInboundRequest,
    RemoveUserOperation,
)
from src.integrations.xray.generated.command_pb2_grpc import HandlerServiceStub
from src.integrations.xray.generated.user_pb2 import User


class XrayGrpcGateway(XrayGateway):
    def __init__(self, api_address: str) -> None:
        self.api_address = api_address
        self._channel = grpc.aio.insecure_channel(api_address)
        self._stub = HandlerServiceStub(self._channel)

    async def list_users(self, inbound_tag: str) -> list[XrayUser]:
        # Xray gRPC API (HandlerService) does not support list_users directly.
        # For now we return an empty list and rely on our DB for truth.
        return []

    async def add_user(self, user: XrayUser) -> None:
        account = VlessAccount(id=user.uuid, flow="xtls-rprx-vision", encryption="none")
        proto_user = User(
            email=user.email,
            level=0,
            account=Any(
                type_url="xray.proxy.vless.Account",
                value=account.SerializeToString(),
            ),
        )
        operation = Any(
            type_url="xray.app.proxyman.command.AddUserOperation",
            value=AddUserOperation(user=proto_user).SerializeToString(),
        )
        await self._stub.AlterInbound(
            AlterInboundRequest(tag=user.inbound_tag, operation=operation)
        )

    async def remove_user(self, inbound_tag: str, email: str) -> None:
        operation = Any(
            type_url="xray.app.proxyman.command.RemoveUserOperation",
            value=RemoveUserOperation(email=email).SerializeToString(),
        )
        await self._stub.AlterInbound(
            AlterInboundRequest(tag=inbound_tag, operation=operation)
        )
