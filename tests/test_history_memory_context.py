from unittest.mock import patch

from chat.service.history_service import build_history_text


# 新会话没有历史，不查询任何 DAO。
with (
    patch(
        "chat.service.history_service.get_conversation_memory",
    ) as get_memory_mock,
    patch(
        "chat.service.history_service.get_recent_messages",
    ) as get_messages_mock,
):
    history = build_history_text(
        user_id=1,
        conversation_id=None,
    )

assert history == "暂无历史对话"
get_memory_mock.assert_not_called()
get_messages_mock.assert_not_called()


# 长期摘要和最近消息被分区组合。
messages = [
    {
        "role": "user",
        "content": "  连续请假需要什么材料？  ",
    },
    {
        "role": "assistant",
        "content": "需要补充相关证明材料。",
    },
    {
        "role": "system",
        "content": "不应进入上下文",
    },
    {
        "role": "assistant",
        "content": "   ",
    },
    {
        "role": "user",
        "content": None,
    },
]

with (
    patch(
        "chat.service.history_service.get_conversation_memory",
        return_value={
            "memory_summary": "  用户正在了解请假制度。  ",
            "summarized_until_message_id": 6,
            "memory_updated_at": "mock-time",
        },
    ) as get_memory_mock,
    patch(
        "chat.service.history_service.get_recent_messages",
        return_value=messages,
    ) as get_messages_mock,
):
    history = build_history_text(
        user_id=1,
        conversation_id=3,
    )

assert history == (
    "长期记忆摘要：\n"
    "用户正在了解请假制度。\n\n"
    "最近对话：\n"
    "用户：连续请假需要什么材料？\n"
    "助手：需要补充相关证明材料。"
)
assert "不应进入上下文" not in history
get_memory_mock.assert_called_once_with(
    user_id=1,
    conversation_id=3,
)
get_messages_mock.assert_called_once_with(
    user_id=1,
    conversation_id=3,
    limit=10,
)


# 没有长期摘要时保留最近对话，并显示摘要为“无”。
with (
    patch(
        "chat.service.history_service.get_conversation_memory",
        return_value={
            "memory_summary": None,
            "summarized_until_message_id": 0,
            "memory_updated_at": None,
        },
    ),
    patch(
        "chat.service.history_service.get_recent_messages",
        return_value=[
            {
                "role": "user",
                "content": "你好",
            },
        ],
    ),
):
    history = build_history_text(
        user_id=1,
        conversation_id=3,
    )

assert history == (
    "长期记忆摘要：\n"
    "无\n\n"
    "最近对话：\n"
    "用户：你好"
)


# 没有最近消息时保留长期摘要，并显示最近对话为“无”。
with (
    patch(
        "chat.service.history_service.get_conversation_memory",
        return_value={
            "memory_summary": "用户偏好简洁回答。",
            "summarized_until_message_id": 6,
            "memory_updated_at": "mock-time",
        },
    ),
    patch(
        "chat.service.history_service.get_recent_messages",
        return_value=[],
    ),
):
    history = build_history_text(
        user_id=1,
        conversation_id=3,
    )

assert history == (
    "长期记忆摘要：\n"
    "用户偏好简洁回答。\n\n"
    "最近对话：\n"
    "无"
)


# 长期摘要和最近消息都为空时保持旧行为。
with (
    patch(
        "chat.service.history_service.get_conversation_memory",
        return_value={
            "memory_summary": "   ",
            "summarized_until_message_id": 0,
            "memory_updated_at": None,
        },
    ),
    patch(
        "chat.service.history_service.get_recent_messages",
        return_value=[],
    ),
):
    history = build_history_text(
        user_id=1,
        conversation_id=3,
    )

assert history == "暂无历史对话"


# 首次读取发现会话不存在时不再查询消息。
with (
    patch(
        "chat.service.history_service.get_conversation_memory",
        return_value=None,
    ),
    patch(
        "chat.service.history_service.get_recent_messages",
    ) as get_messages_mock,
):
    try:
        build_history_text(
            user_id=1,
            conversation_id=999,
        )
        assert False, "会话不存在时应该抛出异常"
    except ValueError as error:
        assert str(error) == "会话不存在"

get_messages_mock.assert_not_called()


# 读取记忆后会话被删除时仍返回明确错误。
with (
    patch(
        "chat.service.history_service.get_conversation_memory",
        return_value={
            "memory_summary": None,
            "summarized_until_message_id": 0,
            "memory_updated_at": None,
        },
    ),
    patch(
        "chat.service.history_service.get_recent_messages",
        return_value=None,
    ),
):
    try:
        build_history_text(
            user_id=1,
            conversation_id=3,
        )
        assert False, "消息查询找不到会话时应该抛出异常"
    except ValueError as error:
        assert str(error) == "会话不存在"


print("长期与短期记忆上下文组合测试通过")
