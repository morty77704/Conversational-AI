from unittest.mock import MagicMock, patch

from chat.dao.conversation_dao import (
    get_conversation_list,
)


connection = MagicMock()
cursor = MagicMock()

connection.cursor.return_value.__enter__.return_value = cursor

cursor.fetchall.return_value = [
    {
        "id": 3,
        "title": "你好，我叫小明",
        "created_at": "mock-created-time",
        "updated_at": "mock-updated-time",
    }
]


with patch(
    "chat.dao.conversation_dao.get_mysql_connection",
    return_value=connection,
):
    result = get_conversation_list(user_id=1)


assert len(result) == 1
assert result[0]["id"] == 3

cursor.execute.assert_called_once()

sql = cursor.execute.call_args.args[0]
params = cursor.execute.call_args.args[1]

assert "user_id = %s" in sql
assert "deleted_at IS NULL" in sql
assert "updated_at DESC" in sql
assert params == (1,)

connection.close.assert_called_once_with()

print("历史会话列表 DAO 测试通过")