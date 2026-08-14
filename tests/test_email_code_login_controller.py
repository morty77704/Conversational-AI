from unittest.mock import patch

from fastapi import HTTPException

from users.controller.user_controller import (
    login_with_email_code,
)
from users.entity.user_entity import (
    EmailCodeLoginRequest,
    LoginResponse,
)


request = EmailCodeLoginRequest(
    email="TEST@example.com",
    email_code="123456",
)

login_response = LoginResponse(
    id=1,
    username="测试用户",
    email="test@example.com",
    access_token="mock-access-token",
    token_type="Bearer",
    expires_in=1800,
)


# 登录成功。
with patch(
    "users.controller.user_controller.login_user_by_email_code",
    return_value=login_response,
) as login_service_mock:
    result = login_with_email_code(request)

    login_service_mock.assert_called_once_with(request)

    assert result.id == 1
    assert result.access_token == "mock-access-token"
    assert result.token_type == "Bearer"


# 验证码错误映射为 401。
with patch(
    "users.controller.user_controller.login_user_by_email_code",
    side_effect=ValueError("验证码错误"),
):
    try:
        login_with_email_code(request)
        assert False, "验证码错误时应该抛出 HTTPException"
    except HTTPException as error:
        assert error.status_code == 401
        assert error.detail == "验证码错误"


# 验证码过期映射为 401。
with patch(
    "users.controller.user_controller.login_user_by_email_code",
    side_effect=ValueError("验证码不存在或已过期"),
):
    try:
        login_with_email_code(request)
        assert False, "验证码过期时应该抛出 HTTPException"
    except HTTPException as error:
        assert error.status_code == 401
        assert error.detail == "验证码不存在或已过期"


# 禁用账号映射为 403。
with patch(
    "users.controller.user_controller.login_user_by_email_code",
    side_effect=ValueError("账号已禁用"),
):
    try:
        login_with_email_code(request)
        assert False, "禁用账号应该抛出 HTTPException"
    except HTTPException as error:
        assert error.status_code == 403
        assert error.detail == "账号已禁用"


print("邮箱验证码登录 Controller 测试通过")