from typing import Any
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from users.entity.user_entity import (
    EmailCodeLoginRequest,
    LoginRequest,
    RegisterRequest,
    UserResponse,
    LoginResponse,
    LogoutResponse,
    MessageResponse,
    SendEmailCodeRequest,
)
from users.service.user_service import (
    login_user,
    register_user,
    login_user_by_email_code,
)
from users.service.auth_service import (
    get_current_auth,
    get_current_user,
    logout_user,
)
from users.service.email_code_service import (
    send_email_code,
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


@user_router.post(
    "/login/email-code",
    response_model=LoginResponse,
)
def login_with_email_code(
        request: EmailCodeLoginRequest,
) -> LoginResponse:
    try:
        return login_user_by_email_code(request)

    except ValueError as error:
        message = str(error)

        unauthorized_messages = {
            "邮箱账号不存在",
            "验证码不存在或已过期",
            "验证码错误",
            "验证码错误次数过多，请重新获取",
        }

        if message in unauthorized_messages:
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
def logout(auth_context: dict[str, Any] = Depends(get_current_auth), ) -> LogoutResponse:
    return logout_user(auth_context)


@user_router.post(
    "/email-codes",
    response_model=MessageResponse,
)
def send_email_code_endpoint(
        request: SendEmailCodeRequest,
) -> MessageResponse:
    try:
        return send_email_code(request)
    except ValueError as error:
        message = str(error)

        if message == "邮箱已注册":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=message,
            ) from error

        if message == "邮箱账号不存在":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            ) from error

        if message == "账号已禁用":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=message,
            ) from error

        if message == "验证码发送过于频繁，请稍后再试":
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=message,
            ) from error

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="邮件服务暂时不可用",
        ) from error
