import smtplib
from email.message import EmailMessage

from common.config import get_settings


def send_email_code(
    recipient_email: str,
    code: str,
    expires_in: int,
) -> None:
    settings = get_settings()

    required_values = [
        settings.smtp_host,
        settings.smtp_username,
        settings.smtp_password,
        settings.smtp_sender_email,
    ]

    if not all(required_values):
        raise RuntimeError("SMTP 配置不完整")

    message = EmailMessage()
    message["From"] = settings.smtp_sender_email
    message["To"] = recipient_email.strip().lower()
    message["Subject"] = "Conversational AI 邮箱验证码"

    # 将秒钟转换成分钟，方便邮件中阅读
    expires_minutes = max(
        1,
        expires_in // 60,
    )

    message.set_content(
        (
            f"你的邮箱验证码是：{code}\n\n"
            f"验证码将在 {expires_minutes} 分钟后失效。"
            "如果不是你本人操作，请忽略此邮件。"
        )
    )

    smtp_class = (
        smtplib.SMTP_SSL
        if settings.smtp_use_ssl
        else smtplib.SMTP
    )

    try:
        with smtp_class(
            host=settings.smtp_host,
            port=settings.smtp_port,
            timeout=settings.smtp_timeout,
        ) as smtp:
            if not settings.smtp_use_ssl:
                smtp.starttls()          # 如果没有建立加密，在此处再次建立加密

            smtp.login(
                settings.smtp_username,
                settings.smtp_password,
            )
            smtp.send_message(message)
    except (smtplib.SMTPException, OSError) as error:
        raise RuntimeError(
            "邮件服务连接或发送失败"
        ) from error
