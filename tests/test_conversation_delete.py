from unittest.mock import MagicMock, patch

from chat.dao.conversation_dao import (
    soft_delete_conversation,
)


connection = MagicMock()
cursor = MagicMock()
connection.cursor.return_value.__enter__.return_value = cursor
cursor.rowcount = 1


with patch(
    "chat.dao.conversation_dao.get_mysql_connection",
    return_value=connection,
):
    deleted = soft_delete_conversation(
        user_id=1,
        conversation_id=3,
    )


assert deleted is True

sql = cursor.execute.call_args.args[0]
params = cursor.execute.call_args.args[1]

assert "user_id = %s" in sql
assert "deleted_at IS NULL" in sql
assert params == (3, 1)

connection.commit.assert_called_once_with()
connection.rollback.assert_not_called()
connection.close.assert_called_once_with()

print("会话软删除 DAO 测试通过")