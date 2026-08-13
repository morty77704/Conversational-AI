import json
import logging
from collections.abc import Iterator

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from users.entity.user_entity import UserResponse
from users.service.auth_service import get_current_user
from chat.dao.conversation_dao import save_chat_round
from chat.entity.intent_entity import IntentType
from chat.service.chat_service import (
    stream_general_chat,
    stream_rag_chat,
)
from chat.service.intent_service import classify_intent
from chat.service.history_service import build_history_text

logger = logging.getLogger(__name__)

chat_router = APIRouter()


def format_sse(data: dict[str, object]) -> str:
    json_data = json.dumps(
        data,
        ensure_ascii=False,
    )

    return f"data: {json_data}\n\n"


def generate_chat_events(
        question: str,
        user_id: int,
        conversation_id: int | None,
) -> Iterator[str]:
    try:
        answer_parts: list[str] = []

        history = build_history_text(
            user_id=user_id,
            conversation_id=conversation_id,
        )

        intent_result = classify_intent(question)

        if intent_result.intent == IntentType.GENERAL_CHAT:
            answer_stream = stream_general_chat(
                question=question,
                history=history,
            )
        else:
            # knowledge_query 和 uncertain 都走保守的 RAG 路线。
            answer_stream = stream_rag_chat(
                question=question,
                history=history,
            )

        for chunk in answer_stream:
            answer_parts.append(chunk)

            yield format_sse(
                {
                    "type": "message",
                    "content": chunk,
                }
            )
        answer = "".join(answer_parts).strip()

        if not answer:
            raise RuntimeError("模型未生成有效回答")

        saved_conversation_id = save_chat_round(
            user_id=user_id,
            question=question,
            answer=answer,
            conversation_id=conversation_id,
        )

        yield format_sse(
            {
                "type": "done",
                "content": "[DONE]",
                "conversation_id": saved_conversation_id,
            }
        )

    except Exception:
        logger.exception("聊天流生成失败")

        yield format_sse(
            {
                "type": "error",
                "content": "回答生成失败",
            }
        )


@chat_router.get("/chat")
def chat(
        question: str = Query(min_length=1),
        conversation_id: int | None = Query(
            default=None,
            gt=0,
        ),
        current_user: UserResponse = Depends(
            get_current_user
        ),
) -> StreamingResponse:
    cleaned_question = question.strip()

    if not cleaned_question:
        raise HTTPException(
            status_code=422,
            detail="问题不能为空",
        )

    return StreamingResponse(
        generate_chat_events(
            question=cleaned_question,
            user_id=current_user.id,
            conversation_id=conversation_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
