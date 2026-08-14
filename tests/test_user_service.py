from unittest.mock import patch

from pymysql.err import IntegrityError

from common.password_util import verify_password
from users.entity.user_entity import (
    EmailCodePurpose,
    RegisterRequest,
)
from users.service.user_service import register_user


request = RegisterRequest(
    username="测试用户",
    email="TEST@example.com",
    password="test-password-123",
    confirm_password="test-password-123",
    email_code="123456",
)


# 正常注册：先验证邮箱验证码，再哈希密码并创建用户。
with (
    patch(
        "users.service.user_service.email_exists",
        return_value=False,
    ),
    patch(
        "users.service.user_service.verify_email_code",
    ) as verify_code_mock,
    patch(
        "users.service.user_service.create_user",
        return_value={
            "id": 1,
            "username": "测试用户",
            "email": "test@example.com",
            "status": 1,
        },
    ) as create_user_mock,
):
    result = register_user(request)

    verify_code_mock.assert_called_once_with(
        email="test@example.com",
        purpose=EmailCodePurpose.REGISTER,
        submitted_code="123456",
    )

    create_arguments = create_user_mock.call_args.kwargs
    saved_hash = create_arguments["password_hash"]

    assert result.id == 1
    assert result.email == "test@example.com"
    assert saved_hash != request.password
    assert verify_password(request.password, saved_hash)
    assert "password_hash" not in result.model_dump()


# 预检查发现邮箱存在时，不验证验证码，也不创建用户。
with (
    patch(
        "users.service.user_service.email_exists",
        return_value=True,
    ),
    patch(
        "users.service.user_service.verify_email_code",
    ) as verify_code_mock,
    patch(
        "users.service.user_service.create_user",
    ) as create_user_mock,
):
    try:
        register_user(request)
        assert False, "邮箱重复时应该抛出异常"
    except ValueError as error:
        assert str(error) == "邮箱已注册"

    verify_code_mock.assert_not_called()
    create_user_mock.assert_not_called()


# 验证码错误时，不创建用户。
with (
    patch(
        "users.service.user_service.email_exists",
        return_value=False,
    ),
    patch(
        "users.service.user_service.verify_email_code",
        side_effect=ValueError("验证码错误"),
    ),
    patch(
        "users.service.user_service.create_user",
    ) as create_user_mock,
):
    try:
        register_user(request)
        assert False, "验证码错误时不应注册"
    except ValueError as error:
        assert str(error) == "验证码错误"

    create_user_mock.assert_not_called()


# 预检查和验证码均通过，但 INSERT 仍可能因并发产生唯一键冲突。
with (
    patch(
        "users.service.user_service.email_exists",
        return_value=False,
    ),
    patch(
        "users.service.user_service.verify_email_code",
    ),
    patch(
        "users.service.user_service.create_user",
        side_effect=IntegrityError(
            1062,
            "Duplicate entry",
        ),
    ),
):
    try:
        register_user(request)
        assert False, "唯一键冲突时应该抛出异常"
    except ValueError as error:
        assert str(error) == "邮箱已注册"


print("用户注册 Service 测试通过")
