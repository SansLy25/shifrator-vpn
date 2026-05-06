import json
import os
import sys
import urllib.parse
import urllib.request


def load_env_file(path: str = ".env") -> None:
    if not os.path.exists(path):
        return

    with open(path, encoding="utf-8") as env_file:
        for line in env_file:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            name, value = stripped.split("=", 1)
            os.environ.setdefault(name, value.strip().strip('"').strip("'"))


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def main() -> None:
    load_env_file()

    bot_token = require_env("BOT_TOKEN")
    webhook_base_url = require_env("WEBHOOK_BASE_URL").rstrip("/")
    webhook_secret = require_env("TELEGRAM_WEBHOOK_SECRET")

    webhook_url = f"{webhook_base_url}/webhooks/telegram/{webhook_secret}"
    telegram_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    payload = urllib.parse.urlencode(
        {
            "url": webhook_url,
            "secret_token": webhook_secret,
            "drop_pending_updates": "true",
        }
    ).encode()

    request = urllib.request.Request(telegram_url, data=payload, method="POST")
    with urllib.request.urlopen(request, timeout=20) as response:
        result = json.loads(response.read().decode())

    print(json.dumps({"webhook_url": webhook_url, "telegram_response": result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Webhook registration failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
