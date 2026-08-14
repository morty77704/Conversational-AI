from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class ConversationSummary(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime


class ConversationDetail(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse]


class DeleteConversationResponse(BaseModel):
    message: str


class RenameConversationRequest(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200,
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("会话标题不能为空")

        return cleaned_value
