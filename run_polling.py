import asyncio
import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.bot.setup import create_dispatcher
from src.core.config import settings
from src.main import create_vpn_link_builder, create_xray_gateway

logging.basicConfig(level=logging.INFO)

async def main() -> None:
    if not settings.bot_token:
        raise ValueError("BOT_TOKEN is not set")

    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    
    # Delete webhook to enable polling
    await bot.delete_webhook(drop_pending_updates=True)

    xray_gateway = create_xray_gateway()
    vpn_link_builder = create_vpn_link_builder()
    
    dispatcher = create_dispatcher(
        xray_gateway=xray_gateway,
        default_inbound_tag=settings.xray_default_inbound_tag,
        vpn_link_builder=vpn_link_builder,
    )

    print("Starting bot in polling mode...")
    await dispatcher.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
