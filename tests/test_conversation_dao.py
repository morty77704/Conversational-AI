from unittest.mock import MagicMock, patch

from chat.dao.conversation_dao import save_chat_round


def create_fake_connection():
    connection = MagicMock()
    cursor = MagicMock()

    connection.cursor.return_value.__enter__.return_value = cursor

    return connection, cursor


connection, cursor = create_fake_connection()
cursor.lastrowid = 11

with patch(
        "chat.dao.conversation_dao.get_mysql_connection",
        return_value=connection,
):
    conversation_id = save_chat_round(
        user_id=1,
        question="第一条问题",
        answer="第一条回答",
    )

assert conversation_id == 11

assert cursor.execute.call_args.args[1] == (
    1,
    "第一条问题",
)

cursor.executemany.assert_called_once()

assert cursor.executemany.call_args.args[1] == [
    (11, "user", "第一条问题"),
    (11, "assistant", "第一条回答"),
]

connection.commit.assert_called_once_with()
connection.rollback.assert_not_called()
connection.close.assert_called_once_with()

print("新会话保存测试通过")
connection, cursor = create_fake_connection()
cursor.fetchone.return_value = None

with patch(
        "chat.dao.conversation_dao.get_mysql_connection",
        return_value=connection,
):
    try:
        save_chat_round(
            user_id=2,
            question="越权问题",
            answer="不应保存",
            conversation_id=11,
        )
        assert False, "会话不存在时应该抛出异常"
    except ValueError as error:
        assert str(error) == "会话不存在"

cursor.executemany.assert_not_called()
connection.commit.assert_not_called()
connection.rollback.assert_called_once_with()
connection.close.assert_called_once_with()

print("会话不存在回滚测试通过")
