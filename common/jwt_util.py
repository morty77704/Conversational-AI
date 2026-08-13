from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt

from common.config import get_settings


def create_access_token(user_id: int) -> dict[str, str | int]:
    settings = get_settings()

    if not settings.jwt_secret_key.strip():
        raise ValueError("JWT_SECRET_KEY 未配置")

    now = datetime.now(timezone.utc)
    expires_in = settings.jwt_access_token_expire_minutes * 60
    expires_at = now + timedelta(seconds=expires_in)
    token_id = uuid4().hex

    payload = {
        "sub": str(user_id),
        "jti": token_id,
        "type": "access",
        "iat": now,
        "exp": expires_at,
    }

    access_token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return {
        "access_token": access_token,
        "token_id": token_id,
        "expires_in": expires_in,
    }


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    if payload.get("type") != "access":
        raise JWTError("Token 类型无效")

    if not payload.get("sub") or not payload.get("jti"):
        raise JWTError("Token 缺少必要字段")

    return payload