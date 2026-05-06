from uuid import UUID

from fastapi import APIRouter, Depends

from src.core.config import settings
from src.core.dependencies import get_user_service, get_vpn_access_service
from src.services.users import UserService
from src.services.vpn_accesses import CreatedVpnAccess, VpnAccessService

router = APIRouter(prefix="/dev", tags=["dev"])


@router.post("/users/{telegram_id}/issue", response_model=None)
async def issue_test_access(
    telegram_id: int,
    user_service: UserService = Depends(get_user_service),
    vpn_access_service: VpnAccessService = Depends(get_vpn_access_service),
) -> CreatedVpnAccess:
    user = await user_service.get_or_create_from_telegram(telegram_id)
    return await vpn_access_service.create_key(user)


@router.get("/users/{telegram_id}/keys", response_model=None)
async def list_test_user_keys(
    telegram_id: int,
    user_service: UserService = Depends(get_user_service),
    vpn_access_service: VpnAccessService = Depends(get_vpn_access_service),
) -> dict[str, object]:
    user = await user_service.get_or_create_from_telegram(telegram_id)
    keys = await vpn_access_service.list_user_keys(user)
    return {
        "telegram_id": telegram_id,
        "keys": [
            {
                "id": key.id,
                "title": key.title,
                "status": key.status,
                "xray_email": key.xray_email,
                "xray_client_uuid": key.xray_client_uuid,
                "xray_inbound_tag": key.xray_inbound_tag,
                "expires_at": key.expires_at,
            }
            for key in keys
        ],
    }


@router.delete("/keys/{access_id}", response_model=None)
async def revoke_test_access(
    access_id: UUID,
    vpn_access_service: VpnAccessService = Depends(get_vpn_access_service),
) -> dict[str, bool]:
    await vpn_access_service.revoke_key(access_id)
    return {"ok": True}


@router.get("/xray/users", response_model=None)
async def list_test_users(
    vpn_access_service: VpnAccessService = Depends(get_vpn_access_service),
) -> dict[str, object]:
    users = await vpn_access_service.list_xray_managed_users()
    return {
        "inbound_tag": settings.xray_default_inbound_tag,
        "users": users,
    }
