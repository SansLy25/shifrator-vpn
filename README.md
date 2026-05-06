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
