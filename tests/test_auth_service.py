from unittest.mock import patch

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from users.service.auth_service import (
    get_current_auth,
    get_current_user,
)


credentials = HTTPAuthorizationCredentials(
    scheme="Bearer",
    credentials="mock-token",
)

payload = {
    "sub": "1",
    "jti": "mock-jti",
    "type": "access",
}

user = {
    "id": 1,
    "username": "测试用户",
    "email": "test@example.com",
    "status": 1,
}


# 正常认证
with (
    patch(
        "users.service.auth_service.decode_access_token",
        return_value=payload,
    ),
    patch(
        "users.service.auth_service.get_token_user_id",
        return_value="1",
    ),
    patch(
        "users.service.auth_service.get_user_by_id",
        return_value=user,
    ),
):
    auth_context = get_current_auth(credentials)
    current_user = get_current_user(auth_context)

    assert auth_context["token_id"] == "mock-jti"
    assert current_user.id == 1
    assert "status" not in current_user.model_dump()

    print("正常认证测试通过")


# Redis 登录状态不存在
with (
    patch(
        "users.service.auth_service.decode_access_token",
        return_value=payload,
    ),
    patch(
        "users.service.auth_service.get_token_user_id",
        return_value=None,
    ),
    patch(
        "users.service.auth_service.get_user_by_id",
    ) as get_user_mock,
):
    try:
        get_current_auth(credentials)
        assert False, "Redis 状态不存在时应该拒绝认证"
    except HTTPException as error:
        assert error.status_code == 401
        assert error.detail == "登录状态已失效"

    assert not get_user_mock.called

    print("Redis 登录状态失效测试通过")


# 缺少 Bearer Token
try:
    get_current_auth(None)
    assert False, "缺少凭证时应该拒绝认证"
except HTTPException as error:
    assert error.status_code == 401
    assert error.detail == "缺少登录凭证"
    assert error.headers == {
        "WWW-Authenticate": "Bearer"
    }

print("缺少登录凭证测试通过")