from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import APIRouter, HTTPException, Request, status

from src.core.config import settings

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/telegram/{secret}")
async def telegram_webhook(secret: str, request: Request) -> dict[str, bool]:
    if secret != settings.telegram_webhook_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid webhook secret")

    bot: Bot | None = getattr(request.app.state, "bot", None)
    dispatcher: Dispatcher | None = getattr(request.app.state, "dispatcher", None)
    if bot is None or dispatcher is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram bot is not configured")

    payload = await request.json()
    print("WEBHOOK PAYLOAD:", payload)
    update = Update.model_validate(payload, context={"bot": bot})
    await dispatcher.feed_update(bot, update)
    return {"ok": True}
