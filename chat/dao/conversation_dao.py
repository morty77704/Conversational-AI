from typing import Any

from common.mysql_util import get_mysql_connection


def save_chat_round(
        user_id: int,
        question: str,
        answer: str,
        conversation_id: int | None = None,
) -> int:
    connection = get_mysql_connection()

    try:
        with connection.cursor() as cursor:
            if conversation_id is None:
                title = question.strip()[:200]

                cursor.execute(
                    """
                    INSERT INTO conversations (
                        user_id,
                        title
                    )
                    VALUES (%s, %s)
                    """,
                    (user_id, title),
                )

                conversation_id = cursor.lastrowid

            else:
                cursor.execute(
                    """
                    SELECT id
                    FROM conversations
                    WHERE id = %s
                      AND user_id = %s
                      AND deleted_at IS NULL
                    LIMIT 1
                    FOR UPDATE
                    """,
                    (conversation_id, user_id),
                )

                if cursor.fetchone() is None:
                    raise ValueError("会话不存在")

                cursor.execute(
                    """
                    UPDATE conversations
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (conversation_id,),
                )

            cursor.executemany(
                """
                INSERT INTO messages (
                    conversation_id,
                    role,
                    content
                )
                VALUES (%s, %s, %s)
                """,
                [
                    (
                        conversation_id,
                        "user",
                        question,
                    ),
                    (
                        conversation_id,
                        "assistant",
                        answer,
                    ),
                ],
            )

        connection.commit()
        return conversation_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_recent_messages(
        user_id: int,
        conversation_id: int,
        limit: int = 10,
) -> list[dict[str, Any]] | None:
    connection = get_mysql_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM conversations
                WHERE id = %s
                  AND user_id = %s
                  AND deleted_at IS NULL
                LIMIT 1
                """,
                (conversation_id, user_id),
            )

            if cursor.fetchone() is None:
                return None

            cursor.execute(
                """
                SELECT
                    recent.role,
                    recent.content
                FROM (
                    SELECT
                        id,
                        role,
                        content,
                        created_at
                    FROM messages
                    WHERE conversation_id = %s
                    ORDER BY created_at DESC, id DESC
                    LIMIT %s
                ) AS recent
                ORDER BY
                    recent.created_at ASC,
                    recent.id ASC
                """,
                (conversation_id, limit),
            )

            return cursor.fetchall()

    finally:
        connection.close()


def get_conversation_memory(
        user_id: int,
        conversation_id: int,
) -> dict[str, Any] | None:
    connection = get_mysql_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    memory_summary,
                    summarized_until_message_id,
                    memory_updated_at
                FROM conversations
                WHERE id = %s
                  AND user_id = %s
                  AND deleted_at IS NULL
                LIMIT 1
                """,
                (conversation_id, user_id),
            )

            return cursor.fetchone()

    finally:
        connection.close()


def get_messages_to_summarize(
        user_id: int,
        conversation_id: int,
        recent_limit: int = 10,
) -> list[dict[str, Any]] | None:
    if recent_limit <= 0:
        raise ValueError("recent_limit 必须大于0")

    connection = get_mysql_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT summarized_until_message_id
                FROM conversations
                WHERE id = %s
                  AND user_id = %s
                  AND deleted_at IS NULL
                LIMIT 1
                """,
                (conversation_id, user_id),
            )

            memory_record = cursor.fetchone()

            if memory_record is None:
                return None

            summarized_until_message_id = (
                memory_record[
                    "summarized_until_message_id"
                ]
                or 0
            )

            cursor.execute(
                """
                SELECT
                    id,
                    role,
                    content,
                    created_at
                FROM messages
                WHERE conversation_id = %s
                  AND id > %s
                ORDER BY created_at DESC, id DESC
                LIMIT %s, 18446744073709551615
                """,
                (
                    conversation_id,
                    summarized_until_message_id,
                    recent_limit,
                ),
            )

            messages = list(cursor.fetchall())
            messages.reverse()

            return messages

    finally:
        connection.close()


def update_conversation_memory(
        user_id: int,
        conversation_id: int,
        memory_summary: str,
        summarized_until_message_id: int,
) -> bool:
    connection = get_mysql_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE conversations
                SET memory_summary = %s,
                    summarized_until_message_id = %s,
                    memory_updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND user_id = %s
                  AND deleted_at IS NULL
                """,
                (
                    memory_summary,
                    summarized_until_message_id,
                    conversation_id,
                    user_id,
                ),
            )

            updated = cursor.rowcount == 1

        connection.commit()
        return updated

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_conversation_list(
        user_id: int,
) -> list[dict[str, Any]]:
    connection = get_mysql_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    title,
                    created_at,
                    updated_at
                FROM conversations
                WHERE user_id = %s
                  AND deleted_at IS NULL
                ORDER BY updated_at DESC, id DESC
                """,
                (user_id,),
            )

            return cursor.fetchall()

    finally:
        connection.close()


def get_conversation_detail(
        user_id: int,
        conversation_id: int,
) -> dict[str, Any] | None:
    connection = get_mysql_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    title,
                    created_at,
                    updated_at
                FROM conversations
                WHERE id = %s
                  AND user_id = %s
                  AND deleted_at IS NULL
                LIMIT 1
                """,
                (conversation_id, user_id),
            )

            conversation = cursor.fetchone()

            if conversation is None:
                return None

            cursor.execute(
                """
                SELECT
                    id,
                    role,
                    content,
                    created_at
                FROM messages
                WHERE conversation_id = %s
                ORDER BY created_at ASC, id ASC
                """,
                (conversation_id,),
            )

            conversation["messages"] = cursor.fetchall()

            return conversation

    finally:
        connection.close()


def soft_delete_conversation(
        user_id: int,
        conversation_id: int,
) -> bool:
    connection = get_mysql_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE conversations
                SET deleted_at = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND user_id = %s
                  AND deleted_at IS NULL
                """,
                (conversation_id, user_id),
            )

            deleted = cursor.rowcount == 1

        connection.commit()
        return deleted

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def rename_conversation(
        user_id: int,
        conversation_id: int,
        title: str,
) -> dict[str, Any] | None:
    connection = get_mysql_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE conversations
                SET title = %s
                WHERE id = %s
                  AND user_id = %s
                  AND deleted_at IS NULL
                """,
                (
                    title,
                    conversation_id,
                    user_id,
                ),
            )

            cursor.execute(
                """
                SELECT
                    id,
                    title,
                    created_at,
                    updated_at
                FROM conversations
                WHERE id = %s
                  AND user_id = %s
                  AND deleted_at IS NULL
                LIMIT 1
                """,
                (
                    conversation_id,
                    user_id,
                ),
            )

            conversation = cursor.fetchone()

        connection.commit()
        return conversation

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
