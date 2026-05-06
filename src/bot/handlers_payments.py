from aiogram import F, Router
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from src.core.config import settings
from src.services.payments import PaymentService
from src.services.users import UserService
from src.services.vpn_accesses import VpnAccessService

router = Router(name="payments")


@router.callback_query(F.data.startswith("topup_"))
async def handle_topup(
    callback: CallbackQuery,
    user_service: UserService,
    payment_service: PaymentService,
) -> None:
    if not callback.message:
        return
    
    if not settings.payment_provider_token:
        await callback.answer("Оплата временно недоступна.", show_alert=True)
        return

    amount_rub = int(callback.data.split("_")[1])
    amount_kopecks = amount_rub * 100

    from src.bot.handlers import require_telegram_user
    telegram_user = require_telegram_user(callback.from_user)
    user = await user_service.get_or_create_from_telegram(telegram_id=telegram_user.id)

    payment = await payment_service.create_payment(user, amount_kopecks)

    prices = [LabeledPrice(label=f"Пополнение на {amount_rub} ₽", amount=amount_kopecks)]

    await callback.message.answer_invoice(
        title="Пополнение баланса",
        description=f"Пополнение баланса в Shifrator VPN на {amount_rub} ₽",
        payload=payment.invoice_payload,
        provider_token=settings.payment_provider_token.get_secret_value(),
        currency="RUB",
        prices=prices,
        start_parameter="topup",
    )
    await callback.answer()


@router.pre_checkout_query()
async def handle_pre_checkout_query(pre_checkout_query: PreCheckoutQuery) -> None:
    print("HANDLING PRE CHECKOUT QUERY")
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def handle_successful_payment(
    message: Message, 
    payment_service: PaymentService,
    user_service: UserService,
    vpn_access_service: VpnAccessService,
) -> None:
    print("HANDLING SUCCESSFUL PAYMENT")
    successful_payment = message.successful_payment
    if not successful_payment:
        return

    payment, subscription_resumed = await payment_service.complete_payment(
        invoice_payload=successful_payment.invoice_payload,
        telegram_payment_charge_id=successful_payment.telegram_payment_charge_id,
        provider_payment_charge_id=successful_payment.provider_payment_charge_id,
    )

    # Сначала получаем обновленного пользователя
    from src.bot.handlers import require_telegram_user, render_main_menu
    from src.bot.keyboards import main_menu_keyboard
    from datetime import timedelta

    telegram_user = require_telegram_user(message.from_user)
    user = await user_service.get_or_create_from_telegram(
        telegram_id=telegram_user.id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
        last_name=telegram_user.last_name,
    )

    amount_rub = successful_payment.total_amount // 100
    msg = f"✅ Баланс успешно пополнен на {amount_rub} ₽!\n"
    if subscription_resumed:
        msg += "🎉 Ваша подписка на VPN была автоматически активирована/продлена!\n"
        
    if user.subscription_expires_at:
        monthly_kopecks = settings.vpn_subscription_monthly_rub * 100
        months_covered = user.balance_kopecks // monthly_kopecks
        total_expires_at = user.subscription_expires_at + timedelta(days=30 * months_covered)
        sub_text = total_expires_at.strftime("%d.%m.%Y")
        msg += f"📅 С учетом текущего баланса подписка продлена до: <b>{sub_text}</b>"

    await message.answer(msg)

    # Повторно отправляем главное меню
    keys = await vpn_access_service.list_user_keys(user)
    has_sub = user.subscription_expires_at is not None
    await message.answer(render_main_menu(user, keys), reply_markup=main_menu_keyboard(has_sub))
