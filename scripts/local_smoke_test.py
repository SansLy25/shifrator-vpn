import json
import os
import sys
import urllib.request


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
TELEGRAM_ID = int(os.getenv("TEST_TELEGRAM_ID", "100001"))


def request_json(method: str, path: str) -> object:
    request = urllib.request.Request(f"{API_BASE_URL}{path}", method=method)
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode())


def main() -> None:
    issued_access = request_json("POST", f"/dev/users/{TELEGRAM_ID}/issue")
    checks = {
        "health": request_json("GET", "/health"),
        "issued_access": issued_access,
        "user_keys": request_json("GET", f"/dev/users/{TELEGRAM_ID}/keys"),
        "managed_users": request_json("GET", "/dev/xray/users"),
    }
    print(json.dumps(checks, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Local smoke test failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
