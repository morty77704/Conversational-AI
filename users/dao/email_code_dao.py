from common.redis_util import get_redis_client

EMAIL_CODE_KEY_PREFIX = "auth:email_code"
EMAIL_CODE_COOLDOWN_KEY_PREFIX = (
    "auth:email_code_cooldown"
)
EMAIL_CODE_ATTEMPTS_KEY_PREFIX = (
    "auth:email_code_attempts"
)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _build_email_code_key(
        email: str,
        purpose: str,
) -> str:
    return (
        f"{EMAIL_CODE_KEY_PREFIX}:"
        f"{purpose}:{_normalize_email(email)}"
    )


def _build_cooldown_key(
        email: str,
        purpose: str,
) -> str:
    return (
        f"{EMAIL_CODE_COOLDOWN_KEY_PREFIX}:"
        f"{purpose}:{_normalize_email(email)}"
    )


def _build_attempts_key(
        email: str,
        purpose: str,
) -> str:
    return (
        f"{EMAIL_CODE_ATTEMPTS_KEY_PREFIX}:"
        f"{purpose}:{_normalize_email(email)}"
    )


def email_code_in_cooldown(
        email: str,
        purpose: str,
) -> bool:
    client = get_redis_client()

    return bool(
        client.exists(
            _build_cooldown_key(
                email=email,
                purpose=purpose,
            )
        )
    )


def save_email_code(
        email: str,
        purpose: str,
        code: str,
        expires_in: int,
        cooldown_in: int,
) -> None:
    client = get_redis_client()
    pipeline = client.pipeline(transaction=True)
    pipeline.delete(
        _build_attempts_key(
            email=email,
            purpose=purpose,
        )
    )
    pipeline.set(
        _build_email_code_key(
            email=email,
            purpose=purpose,
        ),
        code,
        ex=expires_in,
    )
    pipeline.set(
        _build_cooldown_key(
            email=email,
            purpose=purpose,
        ),
        "1",
        ex=cooldown_in,
    )

    pipeline.execute()


def get_email_code(
    email: str,
    purpose: str,
) -> str | None:
    client = get_redis_client()

    return client.get(
        _build_email_code_key(
            email=email,
            purpose=purpose,
        )
    )


def get_email_code_attempts(
    email: str,
    purpose: str,
) -> int:
    client = get_redis_client()

    attempts = client.get(
        _build_attempts_key(
            email=email,
            purpose=purpose,
        )
    )

    if attempts is None:
        return 0

    return int(attempts)


def increment_email_code_attempts(
    email: str,
    purpose: str,
    expires_in: int,
) -> int:
    client = get_redis_client()
    attempts_key = _build_attempts_key(
        email=email,
        purpose=purpose,
    )

    pipeline = client.pipeline(
        transaction=True
    )
    pipeline.incr(attempts_key)
    pipeline.expire(
        attempts_key,
        expires_in,
    )

    results = pipeline.execute()

    return int(results[0])


def delete_email_code_state(
    email: str,
    purpose: str,
) -> bool:
    client = get_redis_client()

    deleted_count = client.delete(
        _build_email_code_key(
            email=email,
            purpose=purpose,
        ),
        _build_attempts_key(
            email=email,
            purpose=purpose,
        ),
    )

    return deleted_count > 0
