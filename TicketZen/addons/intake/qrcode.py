import secrets
import time
from urllib.parse import quote


def generate_pin() -> str:
    return f"{secrets.randbelow(999999):06d}"


def make_payload_url(base_url: str, pin: str) -> str:
    return f"{base_url}/m/{quote(pin)}"


def rotating_payload(base_url: str):
    pin = generate_pin()
    return {"pin": pin, "url": make_payload_url(base_url, pin), "expires_at": int(time.time()) + 300}
