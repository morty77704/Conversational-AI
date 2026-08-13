from common.redis_util import get_redis_client


TOKEN_KEY_PREFIX = "auth:access"


def _build_token_key(token_id: str) -> str:
    return f"{TOKEN_KEY_PREFIX}:{token_id}"


def save_access_token(
    token_id: str,
    user_id: int,
    expires_in: int,
) -> None:
    client = get_redis_client()

    client.set(
        _build_token_key(token_id),
        str(user_id),
        ex=expires_in,
    )


def get_token_user_id(token_id: str) -> str | None:
    client = get_redis_client()

    return client.get(
        _build_token_key(token_id)
    )


def delete_access_token(token_id: str) -> bool:
    client = get_redis_client()

    deleted_count = client.delete(
        _build_token_key(token_id)
    )

    return deleted_count > 0