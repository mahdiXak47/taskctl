import hashlib
import secrets
import time
from pathlib import Path

import jwt
import yaml

TASKCTL_DIR = Path.home() / ".taskctl"
USERS_FILE  = TASKCTL_DIR / "users.yaml"
SECRET_FILE = TASKCTL_DIR / "secret.key"

ACCESS_EXPIRY  = 15 * 60        # 15 minutes
REFRESH_EXPIRY = 7 * 24 * 3600  # 7 days


def _get_secret() -> str:
    if SECRET_FILE.exists():
        return SECRET_FILE.read_text().strip()
    TASKCTL_DIR.mkdir(parents=True, exist_ok=True)
    secret = secrets.token_hex(32)
    SECRET_FILE.write_text(secret)
    SECRET_FILE.chmod(0o600)
    return secret


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 260_000
    ).hex()


def _load_users() -> dict:
    if not USERS_FILE.exists():
        return {}
    with USERS_FILE.open() as f:
        return yaml.safe_load(f) or {}


def _save_users(users: dict) -> None:
    TASKCTL_DIR.mkdir(parents=True, exist_ok=True)
    with USERS_FILE.open("w") as f:
        yaml.dump(users, f, default_flow_style=False, allow_unicode=True)


def register_user(
    username: str,
    password: str,
    first_name: str = "",
    last_name: str = "",
    email: str = "",
) -> None:
    users = _load_users()
    if username in users:
        raise ValueError("Username already taken.")
    salt = secrets.token_hex(16)
    users[username] = {
        "password_hash": _hash_password(password, salt),
        "salt": salt,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
    }
    _save_users(users)


def verify_password(username: str, password: str) -> bool:
    users = _load_users()
    user = users.get(username)
    if not user:
        return False
    return user["password_hash"] == _hash_password(password, user["salt"])


def create_access_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": int(time.time()) + ACCESS_EXPIRY,
        "type": "access",
    }
    return jwt.encode(payload, _get_secret(), algorithm="HS256")


def create_refresh_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": int(time.time()) + REFRESH_EXPIRY,
        "type": "refresh",
    }
    return jwt.encode(payload, _get_secret(), algorithm="HS256")


def verify_token(token: str, token_type: str = "access") -> str | None:
    """Returns username if valid, None otherwise."""
    try:
        payload = jwt.decode(token, _get_secret(), algorithms=["HS256"])
        if payload.get("type") != token_type:
            return None
        return payload.get("sub")
    except jwt.PyJWTError:
        return None
