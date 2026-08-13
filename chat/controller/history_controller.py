from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from chat.entity.conversation_entity import (
    ConversationDetail,
    ConversationSummary,
    DeleteConversationResponse,
)
from chat.service.history_service import (
    delete_conversation,
    get_conversation,
    list_conversations,
)
from users.entity.user_entity import UserResponse
from users.service.auth_service import get_current_user


history_router = APIRouter()


@history_router.get(
    "/history/conversations",
    response_model=list[ConversationSummary],
)
def get_conversations(
        current_user: UserResponse = Depends(
            get_current_user
        ),
) -> list[ConversationSummary]:
    return list_conversations(current_user.id)


@history_router.get(
    "/history/conversations/{conversation_id}",
    response_model=ConversationDetail,
)
def get_conversation_detail_endpoint(
        conversation_id: int,
        current_user: UserResponse = Depends(
            get_current_user
        ),
) -> ConversationDetail:
    try:
        return get_conversation(
            user_id=current_user.id,
            conversation_id=conversation_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@history_router.delete(
    "/history/conversations/{conversation_id}",
    response_model=DeleteConversationResponse,
)
def delete_conversation_endpoint(
        conversation_id: int,
        current_user: UserResponse = Depends(
            get_current_user
        ),
) -> DeleteConversationResponse:
    try:
        return delete_conversation(
            user_id=current_user.id,
            conversation_id=conversation_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
