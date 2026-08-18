from unittest.mock import patch

from chat.service.memory_service import (
    refresh_conversation_memory,
)


memory_record = {
    "memory_summary": "用户正在了解请假制度。",
    "summarized_until_message_id": 6,
    "memory_updated_at": "mock-updated-time",
}

messages = [
    {
        "id": 7,
        "role": "user",
        "content": "连续请假需要什么材料？",
        "created_at": "mock-time-7",
    },
    {
        "id": 10,
        "role": "assistant",
        "content": "需要补充相关证明材料。",
        "created_at": "mock-time-10",
    },
]


# 正常生成新摘要、推进边界并返回 True。
with (
    patch(
        "chat.service.memory_service.get_conversation_memory",
        return_value=memory_record,
    ) as get_memory_mock,
    patch(
        "chat.service.memory_service.get_messages_to_summarize",
        return_value=messages,
    ) as get_messages_mock,
    patch(
        "chat.service.memory_service.summarize_conversation_memory",
        return_value="更新后的长期记忆",
    ) as summarize_mock,
    patch(
        "chat.service.memory_service.update_conversation_memory",
        return_value=True,
    ) as update_memory_mock,
):
    updated = refresh_conversation_memory(
        user_id=1,
        conversation_id=3,
        recent_limit=10,
    )

assert updated is True
get_memory_mock.assert_called_once_with(
    user_id=1,
    conversation_id=3,
)
get_messages_mock.assert_called_once_with(
    user_id=1,
    conversation_id=3,
    recent_limit=10,
)
summarize_mock.assert_called_once_with(
    existing_summary="用户正在了解请假制度。",
    messages=messages,
)
update_memory_mock.assert_called_once_with(
    user_id=1,
    conversation_id=3,
    memory_summary="更新后的长期记忆",
    summarized_until_message_id=10,
)


# 没有候选消息时返回 False，不调用模型或更新数据库。
with (
    patch(
        "chat.service.memory_service.get_conversation_memory",
        return_value=memory_record,
    ),
    patch(
        "chat.service.memory_service.get_messages_to_summarize",
        return_value=[],
    ),
    patch(
        "chat.service.memory_service.summarize_conversation_memory",
    ) as summarize_mock,
    patch(
        "chat.service.memory_service.update_conversation_memory",
    ) as update_memory_mock,
):
    updated = refresh_conversation_memory(
        user_id=1,
        conversation_id=3,
    )

assert updated is False
summarize_mock.assert_not_called()
update_memory_mock.assert_not_called()


# 初次读取时会话不存在，后续步骤都不执行。
with (
    patch(
        "chat.service.memory_service.get_conversation_memory",
        return_value=None,
    ),
    patch(
        "chat.service.memory_service.get_messages_to_summarize",
    ) as get_messages_mock,
    patch(
        "chat.service.memory_service.summarize_conversation_memory",
    ) as summarize_mock,
    patch(
        "chat.service.memory_service.update_conversation_memory",
    ) as update_memory_mock,
):
    try:
        refresh_conversation_memory(
            user_id=1,
            conversation_id=999,
        )
        assert False, "会话不存在时应该抛出异常"
    except ValueError as error:
        assert str(error) == "会话不存在"

get_messages_mock.assert_not_called()
summarize_mock.assert_not_called()
update_memory_mock.assert_not_called()


# 查询候选消息前会话被删除时，不调用模型或更新数据库。
with (
    patch(
        "chat.service.memory_service.get_conversation_memory",
        return_value=memory_record,
    ),
    patch(
        "chat.service.memory_service.get_messages_to_summarize",
        return_value=None,
    ),
    patch(
        "chat.service.memory_service.summarize_conversation_memory",
    ) as summarize_mock,
    patch(
        "chat.service.memory_service.update_conversation_memory",
    ) as update_memory_mock,
):
    try:
        refresh_conversation_memory(
            user_id=1,
            conversation_id=3,
        )
        assert False, "候选查询找不到会话时应该抛出异常"
    except ValueError as error:
        assert str(error) == "会话不存在"

summarize_mock.assert_not_called()
update_memory_mock.assert_not_called()


# 模型总结失败时不能推进数据库边界。
with (
    patch(
        "chat.service.memory_service.get_conversation_memory",
        return_value=memory_record,
    ),
    patch(
        "chat.service.memory_service.get_messages_to_summarize",
        return_value=messages,
    ),
    patch(
        "chat.service.memory_service.summarize_conversation_memory",
        side_effect=RuntimeError("mock model error"),
    ),
    patch(
        "chat.service.memory_service.update_conversation_memory",
    ) as update_memory_mock,
):
    try:
        refresh_conversation_memory(
            user_id=1,
            conversation_id=3,
        )
        assert False, "模型异常时应该继续抛出"
    except RuntimeError as error:
        assert str(error) == "mock model error"

update_memory_mock.assert_not_called()


# 模型完成后会话被删除，更新失败时抛出明确异常。
with (
    patch(
        "chat.service.memory_service.get_conversation_memory",
        return_value=memory_record,
    ),
    patch(
        "chat.service.memory_service.get_messages_to_summarize",
        return_value=messages,
    ),
    patch(
        "chat.service.memory_service.summarize_conversation_memory",
        return_value="更新后的长期记忆",
    ),
    patch(
        "chat.service.memory_service.update_conversation_memory",
        return_value=False,
    ),
):
    try:
        refresh_conversation_memory(
            user_id=1,
            conversation_id=3,
        )
        assert False, "记忆更新失败时应该抛出异常"
    except ValueError as error:
        assert str(error) == "会话不存在或已删除"


print("长期记忆编排测试通过")
