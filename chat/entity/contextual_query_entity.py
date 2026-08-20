from pydantic import BaseModel, Field

from chat.entity.intent_entity import IntentType


class ContextualQueryResult(BaseModel):
    intent: IntentType = Field(
        description="结合历史对话判断出的当前问题意图"
    )
    standalone_query: str = Field(
        min_length=1,
        description="补全上下文后可独立用于检索的问题",
    )
    context_sufficient: bool = Field(
        description="历史对话是否足以消解当前问题中的指代和省略"
    )
    rewrite_needed: bool = Field(
        description="当前问题是否需要借助历史对话才能独立理解"
    )
    history_evidence: list[str] = Field(
        default_factory=list,
        description="改写时从历史对话原样引用的短语",
    )
