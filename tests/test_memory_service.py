from unittest.mock import patch

from langchain_core.runnables import RunnableLambda

from chat.service.memory_service import (
    format_messages_for_summary,
    summarize_conversation_memory,
)


messages = [
    {
        "id": 7,
        "role": "user",
        "content": "  连续请假需要什么材料？  ",
    },
    {
        "id": 8,
        "role": "assistant",
        "content": "需要补充相关证明材料。",
    },
    {
        "id": 9,
        "role": "system",
        "content": "不应进入摘要",
    },
    {
        "id": 10,
        "role": "assistant",
        "content": "   ",
    },
    {
        "id": 11,
        "role": "user",
        "content": None,
    },
]


# 只格式化有效的用户和助手消息。
formatted_messages = format_messages_for_summary(
    messages
)

assert formatted_messages == (
    "用户：连续请假需要什么材料？\n"
    "助手：需要补充相关证明材料。"
)


# 旧摘要和新增消息进入 Prompt，模型结果去除首尾空白。
captured_prompt = {}


def fake_summary_model(prompt_value):
    captured_prompt["text"] = prompt_value.to_string()

    return (
        "  用户正在了解请假制度，特别关注"
        "连续请假所需的证明材料。  "
    )


fake_model = RunnableLambda(fake_summary_model)

with patch(
    "chat.service.memory_service.load_chat_model",
    return_value=fake_model,
) as load_model_mock:
    summary = summarize_conversation_memory(
        existing_summary="用户正在了解公司请假制度。",
        messages=messages,
    )

assert summary == (
    "用户正在了解请假制度，特别关注"
    "连续请假所需的证明材料。"
)
assert "用户正在了解公司请假制度。" in captured_prompt["text"]
assert "用户：连续请假需要什么材料？" in captured_prompt["text"]
assert "助手：需要补充相关证明材料。" in captured_prompt["text"]
assert "不应进入摘要" not in captured_prompt["text"]
load_model_mock.assert_called_once_with()


# 没有有效消息时，不加载模型。
with patch(
    "chat.service.memory_service.load_chat_model",
) as load_model_mock:
    try:
        summarize_conversation_memory(
            existing_summary="已有摘要",
            messages=[
                {
                    "role": "system",
                    "content": "无效角色",
                },
                {
                    "role": "user",
                    "content": "   ",
                },
            ],
        )
        assert False, "没有有效消息时应该抛出异常"
    except ValueError as error:
        assert str(error) == "没有需要总结的消息"

load_model_mock.assert_not_called()


# 模型返回空白内容时抛出明确异常。
blank_model = RunnableLambda(
    lambda _: "   "
)

with patch(
    "chat.service.memory_service.load_chat_model",
    return_value=blank_model,
):
    try:
        summarize_conversation_memory(
            existing_summary=None,
            messages=messages,
        )
        assert False, "模型返回空摘要时应该抛出异常"
    except RuntimeError as error:
        assert str(error) == (
            "模型未生成有效的长期记忆摘要"
        )


print("长期记忆总结 Service 测试通过")
