from unittest.mock import patch

from users.entity.user_entity import EmailCodePurpose
from users.service.email_code_service import (
    generate_email_code,
    verify_email_code,
)


with patch(
    "users.service.email_code_service.secrets.randbelow",
    return_value=42,
):
    code = generate_email_code()

assert code == "000042"


with (
    patch(
        "users.service.email_code_service.get_email_code",
        return_value="123456",
    ),
    patch(
        "users.service.email_code_service.get_email_code_attempts",
        return_value=0,
    ),
    patch(
        "users.service.email_code_service.delete_email_code_state",
    ) as delete_mock,
):
    verify_email_code(
        email="test@example.com",
        purpose=EmailCodePurpose.REGISTER,
        submitted_code="123456",
    )

    delete_mock.assert_called_once_with(
        email="test@example.com",
        purpose="register",
    )


with (
    patch(
        "users.service.email_code_service.get_email_code",
        return_value=None,
    ),
    patch(
        "users.service.email_code_service.increment_email_code_attempts",
    ) as increment_mock,
):
    try:
        verify_email_code(
            email="test@example.com",
            purpose=EmailCodePurpose.LOGIN,
            submitted_code="123456",
        )
        assert False, "过期验证码应该失败"
    except ValueError as error:
        assert str(error) == "验证码不存在或已过期"

    increment_mock.assert_not_called()


with (
    patch(
        "users.service.email_code_service.get_email_code",
        return_value="123456",
    ),
    patch(
        "users.service.email_code_service.get_email_code_attempts",
        return_value=1,
    ),
    patch(
        "users.service.email_code_service.increment_email_code_attempts",
        return_value=2,
    ) as increment_mock,
):
    try:
        verify_email_code(
            email="test@example.com",
            purpose=EmailCodePurpose.LOGIN,
            submitted_code="654321",
        )
        assert False, "错误验证码应该失败"
    except ValueError as error:
        assert str(error) == "验证码错误"

    increment_mock.assert_called_once_with(
        email="test@example.com",
        purpose="login",
        expires_in=300,
    )


with (
    patch(
        "users.service.email_code_service.get_email_code",
        return_value="123456",
    ),
    patch(
        "users.service.email_code_service.get_email_code_attempts",
        return_value=4,
    ),
    patch(
        "users.service.email_code_service.increment_email_code_attempts",
        return_value=5,
    ),
    patch(
        "users.service.email_code_service.delete_email_code_state",
    ) as delete_mock,
):
    try:
        verify_email_code(
            email="test@example.com",
            purpose=EmailCodePurpose.LOGIN,
            submitted_code="654321",
        )
        assert False, "第 5 次错误应该使验证码失效"
    except ValueError as error:
        assert str(error) == "验证码错误次数过多，请重新获取"

    delete_mock.assert_called_once_with(
        email="test@example.com",
        purpose="login",
    )


print("邮箱验证码 Service 测试通过")