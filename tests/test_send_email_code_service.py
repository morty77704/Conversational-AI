from unittest.mock import patch

from users.entity.user_entity import (
    SendEmailCodeRequest,
)
from users.service.email_code_service import (
    send_email_code,
)


register_request = SendEmailCodeRequest(
    email="test@example.com",
    purpose="register",
)


with (
    patch(
        "users.service.email_code_service.email_exists",
        return_value=False,
    ),
    patch(
        "users.service.email_code_service.email_code_in_cooldown",
        return_value=False,
    ),
    patch(
        "users.service.email_code_service.generate_email_code",
        return_value="123456",
    ),
    patch(
        "users.service.email_code_service.send_email_code_message",
    ) as email_mock,
    patch(
        "users.service.email_code_service.save_email_code",
    ) as save_mock,
):
    result = send_email_code(register_request)

    email_mock.assert_called_once_with(
        recipient_email="test@example.com",
        code="123456",
        expires_in=300,
    )

    save_mock.assert_called_once_with(
        email="test@example.com",
        purpose="register",
        code="123456",
        expires_in=300,
        cooldown_in=60,
    )

    assert result.message == "验证码已发送"

with (
    patch(
        "users.service.email_code_service.email_exists",
        return_value=True,
    ),
    patch(
        "users.service.email_code_service.send_email_code_message",
    ) as email_mock,
):
    try:
        send_email_code(register_request)
        assert False, "已注册邮箱不应发送注册验证码"
    except ValueError as error:
        assert str(error) == "邮箱已注册"

    email_mock.assert_not_called()


login_request = SendEmailCodeRequest(
    email="test@example.com",
    purpose="login",
)

user = {
    "id": 1,
    "email": "test@example.com",
    "status": 1,
}

with (
    patch(
        "users.service.email_code_service.get_user_auth_by_email",
        return_value=user,
    ),
    patch(
        "users.service.email_code_service.email_code_in_cooldown",
        return_value=False,
    ),
    patch(
        "users.service.email_code_service.generate_email_code",
        return_value="654321",
    ),
    patch(
        "users.service.email_code_service.send_email_code_message",
    ),
    patch(
        "users.service.email_code_service.save_email_code",
    ) as save_mock,
):
    result = send_email_code(login_request)

    save_mock.assert_called_once_with(
        email="test@example.com",
        purpose="login",
        code="654321",
        expires_in=300,
        cooldown_in=60,
    )

    assert result.message == "验证码已发送"

with (
    patch(
        "users.service.email_code_service.email_exists",
        return_value=False,
    ),
    patch(
        "users.service.email_code_service.email_code_in_cooldown",
        return_value=False,
    ),
    patch(
        "users.service.email_code_service.generate_email_code",
        return_value="123456",
    ),
    patch(
        "users.service.email_code_service.send_email_code_message",
        side_effect=RuntimeError("SMTP 发送失败"),
    ),
    patch(
        "users.service.email_code_service.save_email_code",
    ) as save_mock,
):
    try:
        send_email_code(register_request)
        assert False, "SMTP 失败时 Service 应抛出异常"
    except RuntimeError as error:
        assert str(error) == "SMTP 发送失败"

    save_mock.assert_not_called()

print("发送邮箱验证码 Service 测试通过")