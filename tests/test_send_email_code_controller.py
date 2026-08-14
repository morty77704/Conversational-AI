from unittest.mock import patch

from fastapi import HTTPException

from users.controller.user_controller import (
    send_email_code_endpoint,
)
from users.entity.user_entity import (
    MessageResponse,
    SendEmailCodeRequest,
)


request = SendEmailCodeRequest(
    email="test@example.com",
    purpose="register",
)

success_response = MessageResponse(
    message="验证码已发送",
)


with patch(
    "users.controller.user_controller.send_email_code",
    return_value=success_response,
) as service_mock:
    result = send_email_code_endpoint(request)

    service_mock.assert_called_once_with(request)
    assert result.message == "验证码已发送"


error_cases = [
    ("邮箱已注册", 409),
    ("邮箱账号不存在", 404),
    ("账号已禁用", 403),
    ("验证码发送过于频繁，请稍后再试", 429),
]

for message, expected_status in error_cases:
    with patch(
        "users.controller.user_controller.send_email_code",
        side_effect=ValueError(message),
    ):
        try:
            send_email_code_endpoint(request)
            assert False, f"{message} 应返回 HTTP 错误"
        except HTTPException as error:
            assert error.status_code == expected_status
            assert error.detail == message


with patch(
    "users.controller.user_controller.send_email_code",
    side_effect=RuntimeError(
        "SMTP connection failed"
    ),
):
    try:
        send_email_code_endpoint(request)
        assert False, "SMTP 异常应返回 503"
    except HTTPException as error:
        assert error.status_code == 503
        assert error.detail == "邮件服务暂时不可用"


print("发送邮箱验证码 Controller 测试通过")