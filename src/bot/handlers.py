from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message, User as TelegramUser

from src.bot.callbacks import MenuCallback
from src.bot.keyboards import back_to_main_keyboard, balance_keyboard, keys_menu_keyboard, main_menu_keyboard
from src.models.users import User
from src.models.vpn_accesses import VpnAccess
from src.integrations.xray.link_builder import VpnLinkBuilder
from src.services.users import UserService
from src.services.vpn_accesses import InsufficientFundsError, VpnAccessService, VpnKeyLimitExceededError

router = Router(name="main")


@router.message(CommandStart())
async def handle_start(message: Message, user_service: UserService) -> None:
    telegram_user = require_telegram_user(message.from_user)
    user = await user_service.get_or_create_from_telegram(
        telegram_id=telegram_user.id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
        last_name=telegram_user.last_name,
    )
    await message.answer(render_main_menu(user), reply_markup=main_menu_keyboard())


@router.callback_query(MenuCallback.filter(F.action == "main"))
async def handle_main_menu(
    callback: CallbackQuery,
    callback_data: MenuCallback,
    user_service: UserService,
) -> None:
    telegram_user = require_telegram_user(callback.from_user)
    user = await user_service.get_or_create_from_telegram(
        telegram_id=telegram_user.id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
        last_name=telegram_user.last_name,
    )
    await edit_callback_message(callback, render_main_menu(user), main_menu_keyboard())
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.action == "balance"))
async def handle_balance(
    callback: CallbackQuery,
    callback_data: MenuCallback,
    user_service: UserService,
) -> None:
    telegram_user = require_telegram_user(callback.from_user)
    user = await user_service.get_or_create_from_telegram(telegram_id=telegram_user.id)
    await edit_callback_message(callback, render_balance(user), balance_keyboard())
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.action == "keys"))
async def handle_keys(
    callback: CallbackQuery,
    callback_data: MenuCallback,
    user_service: UserService,
    vpn_access_service: VpnAccessService,
    vpn_link_builder: VpnLinkBuilder,
) -> None:
    telegram_user = require_telegram_user(callback.from_user)
    user = await user_service.get_or_create_from_telegram(telegram_id=telegram_user.id)
    keys = await vpn_access_service.list_user_keys(user)
    await edit_callback_message(
        callback,
        render_keys(user, keys, vpn_link_builder),
        keys_menu_keyboard(can_create_key=len(keys) < user.max_vpn_keys),
    )
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.action == "create_key"))
async def handle_create_key(
    callback: CallbackQuery,
    callback_data: MenuCallback,
    user_service: UserService,
    vpn_access_service: VpnAccessService,
    vpn_link_builder: VpnLinkBuilder,
) -> None:
    telegram_user = require_telegram_user(callback.from_user)
    user = await user_service.get_or_create_from_telegram(telegram_id=telegram_user.id)

    try:
        await vpn_access_service.create_key(user)
    except VpnKeyLimitExceededError:
        await callback.answer("Достигнут лимит ключей.", show_alert=True)
        return
    except InsufficientFundsError:
        await callback.answer("Недостаточно средств для оформления подписки. Пополните баланс.", show_alert=True)
        return

    keys = await vpn_access_service.list_user_keys(user)
    await edit_callback_message(
        callback,
        render_keys(user, keys, vpn_link_builder, header="Ключ создан."),
        keys_menu_keyboard(can_create_key=len(keys) < user.max_vpn_keys),
    )
    await callback.answer("Ключ создан")


@router.message()
async def handle_unknown_message(message: Message) -> None:
    await message.answer("Используй /start, чтобы открыть меню.")


def require_telegram_user(telegram_user: TelegramUser | None) -> TelegramUser:
    if telegram_user is None:
        raise ValueError("Telegram user is required")
    return telegram_user


async def edit_callback_message(callback: CallbackQuery, text: str, reply_markup) -> None:
    if callback.message is None:
        return
    await callback.message.edit_text(text, reply_markup=reply_markup)


def render_main_menu(user: User) -> str:
    sub_text = user.subscription_expires_at.strftime("%d.%m.%Y") if user.subscription_expires_at else "Нет"
    return (
        "👋 <b>Shifrator VPN</b>\n\n"
        f"Баланс: <b>{format_kopecks(user.balance_kopecks)}</b>\n"
        f"Подписка: <b>{sub_text}</b>\n"
        f"Лимит ключей: <b>{user.max_vpn_keys}</b>\n\n"
        "Выбери действие:"
    )


def render_balance(user: User) -> str:
    return (
        "💳 <b>Баланс</b>\n\n"
        f"Доступно: <b>{format_kopecks(user.balance_kopecks)}</b>\n\n"
        "Выберите сумму пополнения:"
    )


def render_keys(
    user: User, keys: list[VpnAccess], vpn_link_builder: VpnLinkBuilder, header: str | None = None
) -> str:
    title = f"✅ <b>{header}</b>\n\n" if header else ""
    if not keys:
        return (
            f"{title}🔑 <b>Мои ключи</b>\n\n"
            "У тебя пока нет VPN-ключей.\n"
            f"Можно создать до <b>{user.max_vpn_keys}</b> ключей."
        )

    lines = [
        f"{title}🔑 <b>Мои ключи</b>",
        "",
        f"Использовано: <b>{len(keys)} из {user.max_vpn_keys}</b>",
        "",
    ]
    for index, key in enumerate(keys, start=1):
        expires_at = key.expires_at.strftime("%d.%m.%Y") if key.expires_at else "без срока"
        link = vpn_link_builder.build(uuid=key.xray_client_uuid, name=key.title)
        lines.extend(
            [
                f"<b>{index}. {key.title}</b>",
                f"Статус: <code>{key.status}</code>",
                f"Истекает: <b>{expires_at}</b>",
                f"Ссылка для подключения:",
                f"<code>{link}</code>",
                "",
            ]
        )
    return "\n".join(lines).strip()


def format_kopecks(amount_kopecks: int) -> str:
    rubles = amount_kopecks // 100
    kopecks = abs(amount_kopecks) % 100
    return f"{rubles}.{kopecks:02d} ₽"
