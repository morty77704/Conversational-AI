from datetime import datetime
from unittest.mock import patch

from chat.entity.conversation_entity import (
    RenameConversationRequest,
)
from chat.service.history_service import (
    rename_conversation,
)


now = datetime.now()

renamed_record = {
    "id": 4,
    "title": "新的会话标题",
    "created_at": now,
    "updated_at": now,
}


request = RenameConversationRequest(
    title="  新的会话标题  ",
)

assert request.title == "新的会话标题"


with patch(
    "chat.service.history_service.rename_conversation_record",
    return_value=renamed_record,
) as dao_mock:
    result = rename_conversation(
        user_id=1,
        conversation_id=4,
        title=request.title,
    )

    dao_mock.assert_called_once_with(
        user_id=1,
        conversation_id=4,
        title="新的会话标题",
    )

    assert result.id == 4
    assert result.title == "新的会话标题"


with patch(
    "chat.service.history_service.rename_conversation_record",
    return_value=None,
):
    try:
        rename_conversation(
            user_id=1,
            conversation_id=999,
            title="新的会话标题",
        )
        assert False, "不存在的会话应该抛出异常"
    except ValueError as error:
        assert str(error) == "会话不存在或已删除"


try:
    RenameConversationRequest(title="   ")
    assert False, "空白标题应该校验失败"
except ValueError:
    pass


print("会话标题重命名 Service 测试通过")