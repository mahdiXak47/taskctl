import hashlib
import secrets
import time
from pathlib import Path

import jwt

from .database import init_db, db_user_exists, db_insert_user, db_get_user, TASKCTL_DIR

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


def register_user(
    username: str,
    password: str,
    first_name: str = "",
    last_name: str = "",
    email: str = "",
) -> None:
    init_db()
    if db_user_exists(username):
        raise ValueError("Username already taken.")
    salt = secrets.token_hex(16)
    from .models import TIMESTAMP_FORMAT
    created_at = time.strftime(TIMESTAMP_FORMAT)
    db_insert_user(
        username=username,
        password_hash=_hash_password(password, salt),
        salt=salt,
        first_name=first_name,
        last_name=last_name,
        email=email,
        created_at=created_at,
    )


def verify_password(username: str, password: str) -> bool:
    init_db()
    user = db_get_user(username)
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
    try:
        payload = jwt.decode(token, _get_secret(), algorithms=["HS256"])
        if payload.get("type") != token_type:
            return None
        return payload.get("sub")
    except jwt.PyJWTError:
        return None
