from chat.dao.conversation_dao import (
    get_conversation_memory,
    get_conversation_detail,
    get_conversation_list,
    get_recent_messages,
    rename_conversation as rename_conversation_record,
    soft_delete_conversation,
)
from chat.entity.conversation_entity import (
    ConversationDetail,
    ConversationSummary,
    DeleteConversationResponse,
)


def build_history_text(
        user_id: int,
        conversation_id: int | None,
) -> str:
    if conversation_id is None:
        return "暂无历史对话"

    memory = get_conversation_memory(
        user_id=user_id,
        conversation_id=conversation_id,
    )

    if memory is None:
        raise ValueError("会话不存在")

    messages = get_recent_messages(
        user_id=user_id,
        conversation_id=conversation_id,
        limit=10,
    )

    if messages is None:
        raise ValueError("会话不存在")

    history_parts: list[str] = []

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

        history_parts.append(
            f"{role_name}：{cleaned_content}"
        )

    memory_summary = memory.get("memory_summary")
    cleaned_summary = (
        memory_summary.strip()
        if isinstance(memory_summary, str)
        else ""
    )
    recent_history = "\n".join(history_parts)

    if not cleaned_summary and not recent_history:
        return "暂无历史对话"

    return (
        "长期记忆摘要：\n"
        f"{cleaned_summary or '无'}\n\n"
        "最近对话：\n"
        f"{recent_history or '无'}"
    )


def list_conversations(
        user_id: int,
) -> list[ConversationSummary]:
    records = get_conversation_list(user_id)

    return [
        ConversationSummary.model_validate(record)
        for record in records
    ]


def get_conversation(
        user_id: int,
        conversation_id: int,
) -> ConversationDetail:
    record = get_conversation_detail(
        user_id=user_id,
        conversation_id=conversation_id,
    )

    if record is None:
        raise ValueError("会话不存在")

    return ConversationDetail.model_validate(record)


def delete_conversation(
    user_id: int,
    conversation_id: int,
) -> DeleteConversationResponse:
    deleted = soft_delete_conversation(
        user_id=user_id,
        conversation_id=conversation_id,
    )

    if not deleted:
        raise ValueError("会话不存在或已删除")

    return DeleteConversationResponse(
        message="会话删除成功"
    )


def rename_conversation(
    user_id: int,
    conversation_id: int,
    title: str,
) -> ConversationSummary:
    record = rename_conversation_record(
        user_id=user_id,
        conversation_id=conversation_id,
        title=title,
    )

    if record is None:
        raise ValueError("会话不存在或已删除")

    return ConversationSummary.model_validate(record)
