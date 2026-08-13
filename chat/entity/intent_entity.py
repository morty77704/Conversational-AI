from enum import Enum

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    KNOWLEDGE_QUERY = "knowledge_query"
    GENERAL_CHAT = "general_chat"
    UNCERTAIN = "uncertain"


class IntentResult(BaseModel):
    intent: IntentType = Field(
        description=(
            "用户问题的意图：企业知识查询、"
            "普通对话或无法确定"
        )
    )