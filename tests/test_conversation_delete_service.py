from unittest.mock import patch

from chat.service.history_service import (
    delete_conversation,
)


with patch(
    "chat.service.history_service.soft_delete_conversation",
    return_value=True,
) as dao_mock:
    result = delete_conversation(
        user_id=1,
        conversation_id=3,
    )

    dao_mock.assert_called_once_with(
        user_id=1,
        conversation_id=3,
    )

    assert result.message == "会话删除成功"

    print("会话删除 Service 测试通过")
with patch(
    "chat.service.history_service.soft_delete_conversation",
    return_value=False,
):
    try:
        delete_conversation(
            user_id=1,
            conversation_id=999,
        )
        assert False, "不存在会话应该抛出异常"
    except ValueError as error:
        assert str(error) == "会话不存在或已删除"

print("会话删除未找到测试通过")