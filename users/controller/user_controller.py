from typing import Any
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from users.entity.user_entity import (
    LoginRequest,
    RegisterRequest,
    UserResponse,
    LoginResponse,
    LogoutResponse
)
from users.service.user_service import (
    login_user,
    register_user,

)
from users.service.auth_service import (
    get_current_auth,
    get_current_user,
    logout_user,
)

user_router = APIRouter()


@user_router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,  # 用户创建成功。
)
def register(request: RegisterRequest) -> UserResponse:
    try:
        return register_user(request)
    except ValueError as error:
        message = str(error)

        if message == "邮箱已注册":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,  # 邮箱与已有用户冲突。
                detail=message,
            ) from error

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,  # 两次密码不一致等业务参数错误。
            detail=message,
        ) from error


@user_router.post(
    "/login",
    response_model=LoginResponse,
)
def login(request: LoginRequest) -> LoginResponse:
    try:
        return login_user(request)
    except ValueError as error:
        message = str(error)

        if message == "邮箱或密码错误":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=message,
            ) from error

        if message == "账号已禁用":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=message,
            ) from error

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        ) from error


@user_router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(current_user: UserResponse = Depends(get_current_user), ) -> UserResponse:
    return current_user


@user_router.post(
    "/logout",
    response_model=LogoutResponse,
)
def logout(auth_context: dict[str, Any] = Depends(get_current_auth),) -> LogoutResponse:
    return logout_user(auth_context)
