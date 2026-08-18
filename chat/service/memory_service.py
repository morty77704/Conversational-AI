from typing import Any

from langchain_core.output_parsers import StrOutputParser

from ai.load_chat_model import load_chat_model
from chat.dao.conversation_dao import (
    get_conversation_memory,
    get_messages_to_summarize,
    update_conversation_memory,
)
from chat.service.prompt_service import memory_summary_prompt


def format_messages_for_summary(
        messages: list[dict[str, Any]],
) -> str:
    formatted_parts: list[str] = []

    for message in messages:
        role = message.get("role")
        content = message.get("content")

        if role == "user":
            role_name = "用户"
        elif role == "assistant":
            role_name = "助手"
        else:
            continue

        if not isinstance(content, str):
            continue

        cleaned_content = content.strip()

        if not cleaned_content:
            continue

        formatted_parts.append(
            f"{role_name}：{cleaned_content}"
        )

    return "\n".join(formatted_parts)


def summarize_conversation_memory(
        existing_summary: str | None,
        messages: list[dict[str, Any]],
) -> str:
    formatted_messages = format_messages_for_summary(
        messages
    )

    if not formatted_messages:
        raise ValueError("没有需要总结的消息")

    chain = (
            memory_summary_prompt
            | load_chat_model()
            | StrOutputParser()
    )

    result = chain.invoke(
        {
            "existing_summary": (
                existing_summary.strip()
                if existing_summary
                and existing_summary.strip()
                else "无"
            ),
            "new_messages": formatted_messages,
        }
    )
    cleaned_result = result.strip()

    if not cleaned_result:
        raise RuntimeError(
            "模型未生成有效的长期记忆摘要"
        )

    return cleaned_result


def refresh_conversation_memory(
        user_id: int,
        conversation_id: int,
        recent_limit: int = 10,
) -> bool:
    memory = get_conversation_memory(
        user_id=user_id,
        conversation_id=conversation_id,
    )

    if memory is None:
        raise ValueError("会话不存在")

    messages = get_messages_to_summarize(
        user_id=user_id,
        conversation_id=conversation_id,
        recent_limit=recent_limit,
    )

    if messages is None:
        raise ValueError("会话不存在")

    if not messages:
        return False

    new_summary = summarize_conversation_memory(
        existing_summary=memory["memory_summary"],
        messages=messages,
    )
    last_message_id = messages[-1]["id"]

    updated = update_conversation_memory(
        user_id=user_id,
        conversation_id=conversation_id,
        memory_summary=new_summary,
        summarized_until_message_id=last_message_id,
    )

    if not updated:
        raise ValueError("会话不存在或已删除")

    return True
