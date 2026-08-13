from typing import Any

from common.mysql_util import get_mysql_connection


def get_user_auth_by_email(
        email: str,
) -> dict[str, Any] | None:
    connection = get_mysql_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    username,
                    email,
                    password_hash,
                    status,
                    created_at,
                    updated_at
                FROM users
                WHERE email = %s
                LIMIT 1
                """,
                (email.strip().lower(),),
            )

            return cursor.fetchone()
    finally:
        connection.close()


def get_user_by_id(
        user_id: int,
) -> dict[str, Any] | None:
    connection = get_mysql_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    username,
                    email,
                    status,
                    created_at,
                    updated_at
                FROM users
                WHERE id = %s
                LIMIT 1
                """,
                (user_id,),
            )

            return cursor.fetchone()
    finally:
        connection.close()


def email_exists(email: str) -> bool:
    connection = get_mysql_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM users
                WHERE email = %s
                LIMIT 1
                """,
                (email.strip().lower(),),
            )

            return cursor.fetchone() is not None
    finally:
        connection.close()


def create_user(
    username: str,
    email: str,
    password_hash: str,
) -> dict[str, Any]:
    connection = get_mysql_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (
                    username,
                    email,
                    password_hash
                )
                VALUES (%s, %s, %s)
                """,
                (
                    username.strip(),
                    email.strip().lower(),
                    password_hash,
                ),
            )

            user_id = cursor.lastrowid
            # 确认能够查询到用户后再提交
            cursor.execute(
                """
                SELECT id, username, email, status, created_at, updated_at
                FROM users
                WHERE id = %s
                LIMIT 1
                """,
                (user_id,),
            )
            user = cursor.fetchone()

        if user is None:
            raise RuntimeError("用户创建后无法读取")
        connection.commit()
        return user

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == '__main__':
    print(email_exists("nobody@example.com"))
    print(get_user_by_id(999999))
