from datetime import datetime
from unittest.mock import patch

from chat.service.history_service import (
    list_conversations,
)


now = datetime.now()

records = [
    {
        "id": 3,
        "title": "你好，我叫小明",
        "created_at": now,
        "updated_at": now,
    }
]


with patch(
    "chat.service.history_service.get_conversation_list",
    return_value=records,
) as dao_mock:
    result = list_conversations(user_id=1)

    dao_mock.assert_called_once_with(1)

    assert len(result) == 1
    assert result[0].id == 3
    assert result[0].title == "你好，我叫小明"

    print("历史会话列表 Service 测试通过")