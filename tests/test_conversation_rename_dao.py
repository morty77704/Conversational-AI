from unittest.mock import MagicMock, patch

from chat.dao.conversation_dao import (
    rename_conversation,
)


connection = MagicMock()
cursor = MagicMock()
connection.cursor.return_value.__enter__.return_value = cursor

renamed_record = {
    "id": 4,
    "title": "新的会话标题",
    "created_at": "mock-created-time",
    "updated_at": "mock-updated-time",
}

cursor.fetchone.return_value = renamed_record

with patch(
    "chat.dao.conversation_dao.get_mysql_connection",
    return_value=connection,
):
    result = rename_conversation(
        user_id=1,
        conversation_id=4,
        title="新的会话标题",
    )


assert result == renamed_record
assert cursor.execute.call_count == 2

update_call = cursor.execute.call_args_list[0]
update_sql = update_call.args[0]
update_params = update_call.args[1]

assert "SET title = %s" in update_sql
assert "user_id = %s" in update_sql
assert "deleted_at IS NULL" in update_sql
assert update_params == (
    "新的会话标题",
    4,
    1,
)

select_call = cursor.execute.call_args_list[1]
select_sql = select_call.args[0]
select_params = select_call.args[1]

assert "user_id = %s" in select_sql
assert "deleted_at IS NULL" in select_sql
assert select_params == (4, 1)

connection.commit.assert_called_once_with()
connection.rollback.assert_not_called()
connection.close.assert_called_once_with()

print("会话标题重命名 DAO 测试通过")