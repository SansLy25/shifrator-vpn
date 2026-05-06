# Архитектура, структура и технологии

## Архитектурный подход

Проект сделан как модульный монолит:

- FastAPI отвечает за HTTP endpoints и Telegram webhook.
- Aiogram отвечает за Telegram UI и обработку updates.
- Services содержат бизнес-логику.
- Repositories изолируют работу с БД.
- Integrations изолируют внешние системы, сейчас Xray.
- Models описывают SQLAlchemy ORM.
- Alembic управляет схемой БД.

Главное правило: Telegram handlers не должны напрямую работать с БД или Xray. Они вызывают сервисы.

## Технологии

- Python `3.13`.
- FastAPI.
- Aiogram `3.27`.
- SQLAlchemy `2.x` async.
- Postgres.
- Alembic.
- Docker Compose.
- Pytest + pytest-asyncio.
- Xray integration через интерфейс `XrayGateway`; локально используется `FakeXrayGateway`.

## Docker

Основной состав `docker-compose.yml`:

- `db` — Postgres `16-alpine`.
- `api` — FastAPI + aiogram webhook app.

Контейнер `api` при старте выполняет:

```bash
alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## Основные директории

```text
src/
  api/                 # FastAPI routers: health, webhooks, dev endpoints
  bot/                 # Aiogram handlers, keyboards, callbacks, middleware
  core/                # config, db, dependencies
  integrations/xray/   # XrayGateway interface, fake, grpc stub
  models/              # SQLAlchemy ORM models
  repositories/        # DB access layer
  services/            # business logic

alembic/
  env.py
  versions/

scripts/
  local_smoke_test.py
  register_telegram_webhook.py

tests/
```

## Ключевые файлы

- `src/main.py` — создает FastAPI app, bot, dispatcher, Xray gateway.
- `src/api/webhooks.py` — endpoint `POST /webhooks/telegram/{secret}`.
- `src/bot/handlers.py` — Telegram UI: `/start`, меню, баланс, ключи.
- `src/bot/middlewares.py` — request/update-scoped SQLAlchemy session и service injection.
- `src/core/config.py` — настройки из `.env`.
- `src/core/db.py` — async SQLAlchemy engine/session factory.
- `src/core/dependencies.py` — FastAPI DI для API endpoints.
- `src/integrations/xray/base.py` — `XrayGateway`, `XrayUser`, prefix helpers.
- `src/integrations/xray/fake.py` — in-memory Xray для разработки.
- `src/integrations/xray/grpc.py` — stub под будущий реальный Xray API.
- `src/services/vpn_accesses.py` — создание/удаление VPN-ключей.
- `src/services/users.py` — создание/обновление Telegram-пользователя.
- `src/services/balances.py` — пополнение и списание баланса.
- `alembic/versions/20260506_1415_0001_initial_schema.py` — начальная схема БД.

## Модели данных

### `User`

Хранит Telegram-пользователя:

- `telegram_id`.
- `username`, `first_name`, `last_name`.
- `balance_kopecks`.
- `max_vpn_keys`, по умолчанию `10`.
- `blocked_at`.

### `VpnAccess`

Хранит VPN-ключ:

- `user_id`.
- `title`.
- `status`: `active`, `disabled`, `expired`, `deleted`.
- `managed_by`, сейчас `"bot"`.
- `xray_inbound_tag`.
- `xray_email`.
- `xray_client_uuid`.
- `expires_at`.
- timestamps последнего включения/отключения.

Важное ограничение:

```text
unique(xray_inbound_tag, xray_email)
```

### `Payment`

Под Telegram Payments:

- `provider`, сейчас `telegram`.
- `status`: `pending`, `succeeded`, `failed`, `refunded`, `canceled`.
- `amount_kopecks`.
- `currency`.
- `invoice_payload`.
- `telegram_payment_charge_id`.
- `provider_payment_charge_id`.
- `paid_at`.

### `BalanceTransaction`

Журнал баланса:

- `type`: `payment`, `subscription_charge`, `refund`, `manual_adjustment`.
- `amount_kopecks`.
- `balance_after_kopecks`.
- optional `payment_id`.
- `comment`.

## Xray integration

Сейчас код не зависит напрямую от конкретного способа управления Xray.

Интерфейс:

```python
class XrayGateway(Protocol):
    async def list_users(self, inbound_tag: str) -> list[XrayUser]: ...
    async def add_user(self, user: XrayUser) -> None: ...
    async def remove_user(self, inbound_tag: str, email: str) -> None: ...
```

Реализации:

- `FakeXrayGateway` — локальная разработка и тесты.
- `XrayGrpcGateway` — заглушка; нужно реализовать после проверки реального Xray/Amnezia config.

## Telegram UI

Текущий UI:

- `/start` создает или обновляет пользователя.
- Главное меню показывает баланс и лимит ключей.
- Inline-кнопки:
  - `🔑 Мои ключи`
  - `💳 Баланс`
  - `➕ Создать ключ`
  - `⬅️ Главное меню`

Callback data описан через `MenuCallback` в `src/bot/callbacks.py`.

## Локальная разработка

`.env` должен содержать:

```text
DEBUG=true
XRAY_GATEWAY=fake
XRAY_DEFAULT_INBOUND_TAG=vless-reality
BOT_TOKEN=...
WEBHOOK_BASE_URL=...
TELEGRAM_WEBHOOK_SECRET=...
```

Smoke-test:

```bash
python scripts/local_smoke_test.py
```

Регистрация webhook после запуска туннеля:

```bash
python scripts/register_telegram_webhook.py
```

## Тесты

Сейчас есть тесты:

- `tests/test_app.py` — healthcheck.
- `tests/test_subscriptions.py` — старый service-level fake Xray тест.
- `tests/test_vpn_accesses.py` — создание ключа, лимит ключей, игнорирование внешних Xray users.

Команда:

```bash
venv\Scripts\python.exe -m pytest tests
```
