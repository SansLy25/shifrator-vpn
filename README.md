# Shifrator VPN Bot

Минимальный каркас Telegram-бота для управления VPN-доступом через FastAPI webhook.

## Запуск

1. Скопируйте переменные окружения:

   ```bash
   cp .env.example .env
   ```

2. Укажите в `.env` реальные `BOT_TOKEN`, `WEBHOOK_BASE_URL` и `TELEGRAM_WEBHOOK_SECRET`.

3. Запустите сервисы:

   ```bash
   docker compose up --build
   ```

## Endpoints

- `GET /health` — проверка доступности API.
- `POST /webhooks/telegram/{TELEGRAM_WEBHOOK_SECRET}` — webhook для Telegram.

Если `WEBHOOK_BASE_URL` задан, приложение при старте автоматически регистрирует webhook в Telegram.

## Локальная разработка

Для разработки без реального Xray используется `XRAY_GATEWAY=fake`. В этом режиме доступны dev endpoints, если `DEBUG=true`.

При запуске контейнера API автоматически применяет миграции Alembic:

```bash
alembic upgrade head
```

Локальный smoke-test:

```bash
python scripts/local_smoke_test.py
```

После запуска туннеля укажите публичный адрес в `WEBHOOK_BASE_URL` и зарегистрируйте webhook:

```bash
python scripts/register_telegram_webhook.py
```

## Модель доступа

- Один Telegram-пользователь может иметь до `max_vpn_keys` VPN-ключей, по умолчанию `10`.
- Приложение управляет только Xray-пользователями с `xray_email`, начинающимся с `bot:`.
- Ключи, созданные AmneziaVPN или вручную без prefix `bot:`, считаются внешними и игнорируются.
- Telegram Payments сохраняются в `payments`, движения баланса — в `balance_transactions`.

## Telegram UI

- Единственная команда пользователя — `/start`.
- Основная навигация построена на inline-кнопках и редактировании одного сообщения.
- Сейчас доступны разделы: главное меню, баланс, список ключей, создание ключа.
- Кнопка пополнения и Telegram Payments будут подключены отдельным шагом.
