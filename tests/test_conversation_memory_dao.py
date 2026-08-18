from unittest.mock import MagicMock, patch

from chat.dao.conversation_dao import (
    get_conversation_memory,
    get_messages_to_summarize,
    update_conversation_memory,
)


def create_fake_connection():
    connection = MagicMock()
    cursor = MagicMock()

    connection.cursor.return_value.__enter__.return_value = cursor

    return connection, cursor


# 正常读取会话长期记忆。
connection, cursor = create_fake_connection()
memory_record = {
    "memory_summary": "用户正在讨论请假流程。",
    "summarized_until_message_id": 12,
    "memory_updated_at": "mock-updated-time",
}
cursor.fetchone.return_value = memory_record

with patch(
    "chat.dao.conversation_dao.get_mysql_connection",
    return_value=connection,
):
    result = get_conversation_memory(
        user_id=1,
        conversation_id=3,
    )

assert result == memory_record

read_sql = cursor.execute.call_args.args[0]
read_params = cursor.execute.call_args.args[1]

assert "memory_summary" in read_sql
assert "summarized_until_message_id" in read_sql
assert "user_id = %s" in read_sql
assert "deleted_at IS NULL" in read_sql
assert read_params == (3, 1)
connection.close.assert_called_once_with()


# 会话不存在或不属于当前用户时返回 None。
connection, cursor = create_fake_connection()
cursor.fetchone.return_value = None

with patch(
    "chat.dao.conversation_dao.get_mysql_connection",
    return_value=connection,
):
    result = get_conversation_memory(
        user_id=2,
        conversation_id=3,
    )

assert result is None
connection.close.assert_called_once_with()


# 正常更新会话长期记忆并提交事务。
connection, cursor = create_fake_connection()
cursor.rowcount = 1

with patch(
    "chat.dao.conversation_dao.get_mysql_connection",
    return_value=connection,
):
    updated = update_conversation_memory(
        user_id=1,
        conversation_id=3,
        memory_summary="更新后的长期记忆",
        summarized_until_message_id=18,
    )

assert updated is True

update_sql = cursor.execute.call_args.args[0]
update_params = cursor.execute.call_args.args[1]

assert "memory_summary = %s" in update_sql
assert "summarized_until_message_id = %s" in update_sql
assert "memory_updated_at = CURRENT_TIMESTAMP" in update_sql
assert "user_id = %s" in update_sql
assert "deleted_at IS NULL" in update_sql
assert update_params == (
    "更新后的长期记忆",
    18,
    3,
    1,
)
connection.commit.assert_called_once_with()
connection.rollback.assert_not_called()
connection.close.assert_called_once_with()


# 更新不到会话时返回 False，但事务仍正常结束。
connection, cursor = create_fake_connection()
cursor.rowcount = 0

with patch(
    "chat.dao.conversation_dao.get_mysql_connection",
    return_value=connection,
):
    updated = update_conversation_memory(
        user_id=2,
        conversation_id=3,
        memory_summary="不应写入的摘要",
        summarized_until_message_id=18,
    )

assert updated is False
connection.commit.assert_called_once_with()
connection.rollback.assert_not_called()
connection.close.assert_called_once_with()


# 数据库异常时回滚并继续抛出异常。
connection, cursor = create_fake_connection()
cursor.execute.side_effect = RuntimeError("mock database error")

with patch(
    "chat.dao.conversation_dao.get_mysql_connection",
    return_value=connection,
):
    try:
        update_conversation_memory(
            user_id=1,
            conversation_id=3,
            memory_summary="摘要",
            summarized_until_message_id=18,
        )
        assert False, "数据库异常时应该继续抛出"
    except RuntimeError as error:
        assert str(error) == "mock database error"

connection.commit.assert_not_called()
connection.rollback.assert_called_once_with()
connection.close.assert_called_once_with()


# 查询尚未总结且不属于最近短期记忆的旧消息。
connection, cursor = create_fake_connection()
cursor.fetchone.return_value = {
    "summarized_until_message_id": 6,
}
cursor.fetchall.return_value = (
    {
        "id": 10,
        "role": "assistant",
        "content": "较新的旧回答",
        "created_at": "mock-time-10",
    },
    {
        "id": 7,
        "role": "user",
        "content": "较早的旧问题",
        "created_at": "mock-time-7",
    },
)

with patch(
    "chat.dao.conversation_dao.get_mysql_connection",
    return_value=connection,
):
    messages = get_messages_to_summarize(
        user_id=1,
        conversation_id=3,
        recent_limit=10,
    )

assert [message["id"] for message in messages] == [7, 10]
assert cursor.execute.call_count == 2

memory_sql = cursor.execute.call_args_list[0].args[0]
memory_params = cursor.execute.call_args_list[0].args[1]
message_sql = cursor.execute.call_args_list[1].args[0]
message_params = cursor.execute.call_args_list[1].args[1]

assert "summarized_until_message_id" in memory_sql
assert "user_id = %s" in memory_sql
assert "deleted_at IS NULL" in memory_sql
assert memory_params == (3, 1)
assert "id > %s" in message_sql
assert "ORDER BY created_at DESC, id DESC" in message_sql
assert "LIMIT %s" in message_sql
assert message_params == (3, 6, 10)
connection.close.assert_called_once_with()


# 会话不存在时不执行消息查询。
connection, cursor = create_fake_connection()
cursor.fetchone.return_value = None

with patch(
    "chat.dao.conversation_dao.get_mysql_connection",
    return_value=connection,
):
    messages = get_messages_to_summarize(
        user_id=2,
        conversation_id=3,
    )

assert messages is None
cursor.execute.assert_called_once()
cursor.fetchall.assert_not_called()
connection.close.assert_called_once_with()


# 没有超过短期记忆范围的消息时返回空列表。
connection, cursor = create_fake_connection()
cursor.fetchone.return_value = {
    "summarized_until_message_id": 12,
}
cursor.fetchall.return_value = []

with patch(
    "chat.dao.conversation_dao.get_mysql_connection",
    return_value=connection,
):
    messages = get_messages_to_summarize(
        user_id=1,
        conversation_id=3,
    )

assert messages == []
assert cursor.execute.call_count == 2
connection.close.assert_called_once_with()


# 非正数短期记忆限制直接拒绝，不创建数据库连接。
with patch(
    "chat.dao.conversation_dao.get_mysql_connection",
) as get_connection_mock:
    try:
        get_messages_to_summarize(
            user_id=1,
            conversation_id=3,
            recent_limit=0,
        )
        assert False, "recent_limit 非正数时应该抛出异常"
    except ValueError as error:
        assert str(error) == "recent_limit 必须大于0"

get_connection_mock.assert_not_called()


print("会话长期记忆 DAO 测试通过")
