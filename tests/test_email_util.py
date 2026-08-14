from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from common.email_util import send_email_code


settings = SimpleNamespace(
    smtp_host="smtp.example.com",
    smtp_port=465,
    smtp_username="smtp-user",
    smtp_password="smtp-password",
    smtp_sender_email="sender@example.com",
    smtp_use_ssl=True,
    smtp_timeout=10,
)

smtp = MagicMock()
smtp_context = MagicMock()
smtp_context.__enter__.return_value = smtp

with (
    patch(
        "common.email_util.get_settings",
        return_value=settings,
    ),
    patch(
        "common.email_util.smtplib.SMTP_SSL",
        return_value=smtp_context,
    ) as smtp_class_mock,
):
    send_email_code(
        recipient_email="  TEST@example.com  ",
        code="123456",
        expires_in=300,
    )


smtp_class_mock.assert_called_once_with(
    host="smtp.example.com",
    port=465,
    timeout=10,
)

smtp.login.assert_called_once_with(
    "smtp-user",
    "smtp-password",
)

smtp.send_message.assert_called_once()

message = smtp.send_message.call_args.args[0]

assert message["From"] == "sender@example.com"
assert message["To"] == "test@example.com"
assert message["Subject"] == (
    "Conversational AI 邮箱验证码"
)

content = message.get_content()

assert "123456" in content
assert "5 分钟" in content


starttls_settings = SimpleNamespace(
    smtp_host="smtp.example.com",
    smtp_port=587,
    smtp_username="smtp-user",
    smtp_password="smtp-password",
    smtp_sender_email="sender@example.com",
    smtp_use_ssl=False,
    smtp_timeout=10,
)

starttls_smtp = MagicMock()
starttls_context = MagicMock()
starttls_context.__enter__.return_value = (
    starttls_smtp
)

with (
    patch(
        "common.email_util.get_settings",
        return_value=starttls_settings,
    ),
    patch(
        "common.email_util.smtplib.SMTP",
        return_value=starttls_context,
    ) as smtp_class_mock,
):
    send_email_code(
        recipient_email="test@example.com",
        code="654321",
        expires_in=300,
    )

smtp_class_mock.assert_called_once_with(
    host="smtp.example.com",
    port=587,
    timeout=10,
)
starttls_smtp.starttls.assert_called_once_with()
starttls_smtp.login.assert_called_once_with(
    "smtp-user",
    "smtp-password",
)
starttls_smtp.send_message.assert_called_once()


disconnected_smtp = MagicMock()
disconnected_smtp.login.side_effect = (
    __import__("smtplib").SMTPServerDisconnected(
        "connection closed"
    )
)
disconnected_context = MagicMock()
disconnected_context.__enter__.return_value = (
    disconnected_smtp
)

with (
    patch(
        "common.email_util.get_settings",
        return_value=settings,
    ),
    patch(
        "common.email_util.smtplib.SMTP_SSL",
        return_value=disconnected_context,
    ),
):
    try:
        send_email_code(
            recipient_email="test@example.com",
            code="123456",
            expires_in=300,
        )
        assert False, "SMTP 断开时应该转换异常"
    except RuntimeError as error:
        assert str(error) == "邮件服务连接或发送失败"


incomplete_settings = SimpleNamespace(
    smtp_host="",
    smtp_port=465,
    smtp_username="",
    smtp_password="",
    smtp_sender_email="",
    smtp_use_ssl=False,
    smtp_timeout=10,
)

with patch(
    "common.email_util.get_settings",
    return_value=incomplete_settings,
):
    try:
        send_email_code(
            recipient_email="test@example.com",
            code="123456",
            expires_in=300,
        )
        assert False, "SMTP 配置不完整时应该失败"
    except RuntimeError as error:
        assert str(error) == "SMTP 配置不完整"


print("邮件发送工具测试通过")
