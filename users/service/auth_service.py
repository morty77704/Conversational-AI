from typing import Any, NoReturn   # 形参任意类型，函数不返回

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jose import JWTError
from jose.exceptions import ExpiredSignatureError

from common.jwt_util import decode_access_token
from users.dao.auth_dao import (
    delete_access_token,
    get_token_user_id,
)
from users.dao.user_dao import get_user_by_id
from users.entity.user_entity import (
    LogoutResponse,
    UserResponse,
)


bearer_scheme = HTTPBearer(auto_error=False)


def _raise_unauthorized(message: str) -> NoReturn:  # 封装统一的401代码
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
) -> dict[str, Any]:
    if credentials is None:
        _raise_unauthorized("缺少登录凭证")

    if credentials.scheme.lower() != "bearer":
        _raise_unauthorized("登录凭证格式错误")

    try:
        payload = decode_access_token(
            credentials.credentials
        )
    except ExpiredSignatureError:
        _raise_unauthorized("登录状态已过期")
    except JWTError:
        _raise_unauthorized("登录凭证无效")

    user_id_text = payload["sub"]
    token_id = payload["jti"]

    redis_user_id = get_token_user_id(token_id)

    if redis_user_id is None:
        _raise_unauthorized("登录状态已失效")

    if redis_user_id != user_id_text:
        _raise_unauthorized("登录凭证与用户不匹配")

    try:
        user_id = int(user_id_text)
    except (TypeError, ValueError):
        _raise_unauthorized("登录凭证中的用户ID无效")

    user = get_user_by_id(user_id)

    if user is None:
        _raise_unauthorized("用户不存在")

    if user["status"] != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已禁用",
        )

    return {
        "user": user,
        "token_id": token_id,
        "payload": payload,
    }


def get_current_user(
    auth_context: dict[str, Any] = Depends(
        get_current_auth
    ),
) -> UserResponse:
    return UserResponse.model_validate(
        auth_context["user"]
    )


def logout_user(
    auth_context: dict[str, Any],
) -> LogoutResponse:
    delete_access_token(
        auth_context["token_id"]
    )

    return LogoutResponse(
        message="退出登录成功"
    )