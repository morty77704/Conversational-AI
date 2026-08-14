from unittest.mock import patch

from users.entity.user_entity import (
    EmailCodeLoginRequest,
    EmailCodePurpose,
)
from users.service.user_service import (
    login_user_by_email_code,
)


request = EmailCodeLoginRequest(
    email="TEST@example.com",
    email_code="123456",
)

active_user = {
    "id": 1,
    "username": "测试用户",
    "email": "test@example.com",
    "password_hash": "$2b$12$mock",
    "status": 1,
}

disabled_user = {
    "id": 2,
    "username": "禁用用户",
    "email": "disabled@example.com",
    "password_hash": "$2b$12$mock",
    "status": 0,
}

token_result = {
    "access_token": "mock-access-token",
    "token_id": "mock-token-id",
    "expires_in": 1800,
}


# 场景一：验证码正确，成功创建登录状态。
with (
    patch(
        "users.service.user_service.get_user_auth_by_email",
        return_value=active_user,
    ) as get_user_mock,
    patch(
        "users.service.user_service.verify_email_code",
    ) as verify_code_mock,
    patch(
        "users.service.user_service.create_access_token",
        return_value=token_result,
    ) as create_token_mock,
    patch(
        "users.service.user_service.save_access_token",
    ) as save_token_mock,
):
    result = login_user_by_email_code(request)

    get_user_mock.assert_called_once_with(
        "test@example.com"
    )

    verify_code_mock.assert_called_once_with(
        email="test@example.com",
        purpose=EmailCodePurpose.LOGIN,
        submitted_code="123456",
    )

    create_token_mock.assert_called_once_with(1)

    save_token_mock.assert_called_once_with(
        token_id="mock-token-id",
        user_id=1,
        expires_in=1800,
    )

    assert result.id == 1
    assert result.username == "测试用户"
    assert result.email == "test@example.com"
    assert result.access_token == "mock-access-token"
    assert result.token_type == "Bearer"
    assert result.expires_in == 1800
    assert "password_hash" not in result.model_dump()


# 场景二：用户不存在时，不验证验证码，也不创建 Token。
with (
    patch(
        "users.service.user_service.get_user_auth_by_email",
        return_value=None,
    ),
    patch(
        "users.service.user_service.verify_email_code",
    ) as verify_code_mock,
    patch(
        "users.service.user_service.create_access_token",
    ) as create_token_mock,
    patch(
        "users.service.user_service.save_access_token",
    ) as save_token_mock,
):
    try:
        login_user_by_email_code(request)
        assert False, "用户不存在时应该抛出异常"
    except ValueError as error:
        assert str(error) == "邮箱账号不存在"

    verify_code_mock.assert_not_called()
    create_token_mock.assert_not_called()
    save_token_mock.assert_not_called()


# 场景三：账号禁用时，不消耗验证码，也不创建 Token。
disabled_request = EmailCodeLoginRequest(
    email="disabled@example.com",
    email_code="123456",
)

with (
    patch(
        "users.service.user_service.get_user_auth_by_email",
        return_value=disabled_user,
    ),
    patch(
        "users.service.user_service.verify_email_code",
    ) as verify_code_mock,
    patch(
        "users.service.user_service.create_access_token",
    ) as create_token_mock,
    patch(
        "users.service.user_service.save_access_token",
    ) as save_token_mock,
):
    try:
        login_user_by_email_code(
            disabled_request
        )
        assert False, "禁用账号应该抛出异常"
    except ValueError as error:
        assert str(error) == "账号已禁用"

    verify_code_mock.assert_not_called()
    create_token_mock.assert_not_called()
    save_token_mock.assert_not_called()


# 场景四：验证码错误时，不创建 Token。
with (
    patch(
        "users.service.user_service.get_user_auth_by_email",
        return_value=active_user,
    ),
    patch(
        "users.service.user_service.verify_email_code",
        side_effect=ValueError("验证码错误"),
    ),
    patch(
        "users.service.user_service.create_access_token",
    ) as create_token_mock,
    patch(
        "users.service.user_service.save_access_token",
    ) as save_token_mock,
):
    try:
        login_user_by_email_code(request)
        assert False, "验证码错误时应该抛出异常"
    except ValueError as error:
        assert str(error) == "验证码错误"

    create_token_mock.assert_not_called()
    save_token_mock.assert_not_called()


print("邮箱验证码登录 Service 测试通过")