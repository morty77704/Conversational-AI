from datetime import datetime
from unittest.mock import patch

from fastapi import HTTPException

from chat.controller.history_controller import (
    rename_conversation_endpoint,
)
from chat.entity.conversation_entity import (
    ConversationSummary,
    RenameConversationRequest,
)
from users.entity.user_entity import UserResponse


now = datetime.now()

current_user = UserResponse(
    id=1,
    username="test-user",
    email="test@example.com",
)

request = RenameConversationRequest(
    title="新的会话标题",
)

renamed_conversation = ConversationSummary(
    id=4,
    title="新的会话标题",
    created_at=now,
    updated_at=now,
)


with patch(
    "chat.controller.history_controller.rename_conversation",
    return_value=renamed_conversation,
) as service_mock:
    result = rename_conversation_endpoint(
        conversation_id=4,
        request=request,
        current_user=current_user,
    )

    service_mock.assert_called_once_with(
        user_id=1,
        conversation_id=4,
        title="新的会话标题",
    )

    assert result.id == 4
    assert result.title == "新的会话标题"


with patch(
    "chat.controller.history_controller.rename_conversation",
    side_effect=ValueError("会话不存在或已删除"),
):
    try:
        rename_conversation_endpoint(
            conversation_id=999,
            request=request,
            current_user=current_user,
        )
        assert False, "不存在的会话应该返回 404"
    except HTTPException as error:
        assert error.status_code == 404
        assert error.detail == "会话不存在或已删除"


print("会话标题重命名 Controller 测试通过")