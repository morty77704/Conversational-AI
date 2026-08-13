import bcrypt


BCRYPT_MAX_PASSWORD_BYTES = 72


def _encode_password(password: str) -> bytes:
    password_bytes = password.encode("utf-8")

    if not password_bytes:
        raise ValueError("密码不能为空")

    if len(password_bytes) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError(
            "密码的 UTF-8 编码不能超过 72 字节"
        )

    return password_bytes


def hash_password(password: str) -> str:
    password_bytes = _encode_password(password)

    password_hash = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt(),
    )

    return password_hash.decode("utf-8")


def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    try:
        password_bytes = _encode_password(password)

        return bcrypt.checkpw(
            password_bytes,
            password_hash.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False

