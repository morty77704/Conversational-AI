import json
from unittest.mock import patch

from chat.controller.chat_controller import (
    generate_chat_events,
)
from chat.entity.intent_entity import (
    IntentResult,
    IntentType,
)


def parse_sse_event(event: str) -> dict:
    assert event.startswith("data: ")

    return json.loads(event.removeprefix("data: ").strip())


intent_result = IntentResult(
    intent=IntentType.GENERAL_CHAT
)


# 续聊保存成功后更新记忆，再发送 done。
call_order: list[str] = []


def save_round(*args, **kwargs):
    call_order.append("save")

    return 3


def refresh_memory(*args, **kwargs):
    call_order.append("refresh")

    return True


with (
    patch(
        "chat.controller.chat_controller.build_history_text",
        return_value="mock history",
    ),
    patch(
        "chat.controller.chat_controller.classify_intent",
        return_value=intent_result,
    ),
    patch(
        "chat.controller.chat_controller.stream_general_chat",
        return_value=iter(["回答", "内容"]),
    ),
    patch(
        "chat.controller.chat_controller.stream_rag_chat",
    ) as rag_stream_mock,
    patch(
        "chat.controller.chat_controller.save_chat_round",
        side_effect=save_round,
    ) as save_round_mock,
    patch(
        "chat.controller.chat_controller.refresh_conversation_memory",
        side_effect=refresh_memory,
    ) as refresh_memory_mock,
):
    events = list(
        generate_chat_events(
            question="测试问题",
            user_id=1,
            conversation_id=3,
        )
    )

parsed_events = [
    parse_sse_event(event)
    for event in events
]

assert [event["type"] for event in parsed_events] == [
    "message",
    "message",
    "done",
]
assert parsed_events[0]["content"] == "回答"
assert parsed_events[1]["content"] == "内容"
assert parsed_events[2]["conversation_id"] == 3
assert call_order == ["save", "refresh"]
rag_stream_mock.assert_not_called()
save_round_mock.assert_called_once_with(
    user_id=1,
    question="测试问题",
    answer="回答内容",
    conversation_id=3,
)
refresh_memory_mock.assert_called_once_with(
    user_id=1,
    conversation_id=3,
    recent_limit=10,
)


# 新会话第一轮保存后不执行无意义的记忆刷新。
with (
    patch(
        "chat.controller.chat_controller.build_history_text",
        return_value="暂无历史对话",
    ),
    patch(
        "chat.controller.chat_controller.classify_intent",
        return_value=intent_result,
    ),
    patch(
        "chat.controller.chat_controller.stream_general_chat",
        return_value=iter(["第一轮回答"]),
    ),
    patch(
        "chat.controller.chat_controller.save_chat_round",
        return_value=11,
    ),
    patch(
        "chat.controller.chat_controller.refresh_conversation_memory",
    ) as refresh_memory_mock,
):
    events = list(
        generate_chat_events(
            question="第一轮问题",
            user_id=1,
            conversation_id=None,
        )
    )

parsed_events = [
    parse_sse_event(event)
    for event in events
]

assert parsed_events[-1] == {
    "type": "done",
    "content": "[DONE]",
    "conversation_id": 11,
}
refresh_memory_mock.assert_not_called()


# 当前没有候选旧消息时仍正常发送 done。
with (
    patch(
        "chat.controller.chat_controller.build_history_text",
        return_value="mock history",
    ),
    patch(
        "chat.controller.chat_controller.classify_intent",
        return_value=intent_result,
    ),
    patch(
        "chat.controller.chat_controller.stream_general_chat",
        return_value=iter(["正常回答"]),
    ),
    patch(
        "chat.controller.chat_controller.save_chat_round",
        return_value=3,
    ),
    patch(
        "chat.controller.chat_controller.refresh_conversation_memory",
        return_value=False,
    ),
):
    events = list(
        generate_chat_events(
            question="测试问题",
            user_id=1,
            conversation_id=3,
        )
    )

parsed_events = [
    parse_sse_event(event)
    for event in events
]

assert [event["type"] for event in parsed_events] == [
    "message",
    "done",
]


# 记忆更新异常被隔离，回答仍以 done 正常结束。
with (
    patch(
        "chat.controller.chat_controller.build_history_text",
        return_value="mock history",
    ),
    patch(
        "chat.controller.chat_controller.classify_intent",
        return_value=intent_result,
    ),
    patch(
        "chat.controller.chat_controller.stream_general_chat",
        return_value=iter(["正常回答"]),
    ),
    patch(
        "chat.controller.chat_controller.save_chat_round",
        return_value=3,
    ),
    patch(
        "chat.controller.chat_controller.refresh_conversation_memory",
        side_effect=RuntimeError("mock memory error"),
    ),
    patch(
        "chat.controller.chat_controller.logger.exception",
    ) as logger_mock,
):
    events = list(
        generate_chat_events(
            question="测试问题",
            user_id=1,
            conversation_id=3,
        )
    )

parsed_events = [
    parse_sse_event(event)
    for event in events
]

assert [event["type"] for event in parsed_events] == [
    "message",
    "done",
]
assert all(
    event["type"] != "error"
    for event in parsed_events
)
logger_mock.assert_called_once_with(
    "会话长期记忆更新失败：conversation_id=%s",
    3,
)


# 聊天保存失败时不刷新记忆，并返回 error。
with (
    patch(
        "chat.controller.chat_controller.build_history_text",
        return_value="mock history",
    ),
    patch(
        "chat.controller.chat_controller.classify_intent",
        return_value=intent_result,
    ),
    patch(
        "chat.controller.chat_controller.stream_general_chat",
        return_value=iter(["已经生成的回答"]),
    ),
    patch(
        "chat.controller.chat_controller.save_chat_round",
        side_effect=RuntimeError("mock save error"),
    ),
    patch(
        "chat.controller.chat_controller.refresh_conversation_memory",
    ) as refresh_memory_mock,
    patch(
        "chat.controller.chat_controller.logger.exception",
    ) as logger_mock,
):
    events = list(
        generate_chat_events(
            question="测试问题",
            user_id=1,
            conversation_id=3,
        )
    )

parsed_events = [
    parse_sse_event(event)
    for event in events
]

assert [event["type"] for event in parsed_events] == [
    "message",
    "error",
]
assert parsed_events[-1]["content"] == "回答生成失败"
refresh_memory_mock.assert_not_called()
logger_mock.assert_called_once_with("聊天流生成失败")


print("聊天长期记忆接入测试通过")
