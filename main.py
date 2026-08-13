from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from users.controller.user_controller import user_router
from health.controller import health_router
from common.config import get_settings
from chat.controller.chat_controller import chat_router
from chat.controller.history_controller import history_router

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    router=health_router,
    prefix="/health",
    tags=["健康检测"],
)

app.include_router(
    router=chat_router,
    prefix="/chat",
    tags=["聊天"],
)
app.include_router(
    router=user_router,
    prefix="/users",
    tags=["用户"],
)

app.include_router(
    router=history_router,
    prefix="/chat",
    tags=["历史会话"],
)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=False,
    )