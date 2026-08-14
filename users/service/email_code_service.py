import hmac
import secrets

from common.email_util import (
    send_email_code as send_email_code_message,
)
from users.dao.email_code_dao import (
    delete_email_code_state,
    email_code_in_cooldown,
    get_email_code,
    get_email_code_attempts,
    increment_email_code_attempts,
    save_email_code,
)
from users.dao.user_dao import (
    email_exists,
    get_user_auth_by_email,
)
from users.entity.user_entity import (
    EmailCodePurpose,
    MessageResponse,
    SendEmailCodeRequest,
)

EMAIL_CODE_EXPIRES_IN = 300
EMAIL_CODE_MAX_ATTEMPTS = 5
EMAIL_CODE_COOLDOWN_IN = 60


def generate_email_code() -> str:
    number = secrets.randbelow(1_000_000)

    return f"{number:06d}"


def verify_email_code(
        email: str,
        purpose: EmailCodePurpose,
        submitted_code: str,
) -> None:
    purpose_value = purpose.value

    stored_code = get_email_code(
        email=email,
        purpose=purpose_value,
    )

    if stored_code is None:
        raise ValueError("验证码不存在或已过期")

    attempts = get_email_code_attempts(
        email=email,
        purpose=purpose_value,
    )

    if attempts >= EMAIL_CODE_MAX_ATTEMPTS:
        delete_email_code_state(
            email=email,
            purpose=purpose_value,
        )
        raise ValueError(
            "验证码错误次数过多，请重新获取"
        )

    if not hmac.compare_digest(
            stored_code,
            submitted_code,
    ):
        current_attempts = (
            increment_email_code_attempts(
                email=email,
                purpose=purpose_value,
                expires_in=EMAIL_CODE_EXPIRES_IN,
            )
        )

        if current_attempts >= EMAIL_CODE_MAX_ATTEMPTS:
            delete_email_code_state(
                email=email,
                purpose=purpose_value,
            )
            raise ValueError(
                "验证码错误次数过多，请重新获取"
            )

        raise ValueError("验证码错误")

    delete_email_code_state(
        email=email,
        purpose=purpose_value,
    )


def send_email_code(
    request: SendEmailCodeRequest,
) -> MessageResponse:
    email = str(request.email)
    purpose = request.purpose
    purpose_value = purpose.value

    if purpose == EmailCodePurpose.REGISTER:
        if email_exists(email):
            raise ValueError("邮箱已注册")

    elif purpose == EmailCodePurpose.LOGIN:
        user = get_user_auth_by_email(email)

        if user is None:
            raise ValueError("邮箱账号不存在")

        if user["status"] != 1:
            raise ValueError("账号已禁用")

    if email_code_in_cooldown(
        email=email,
        purpose=purpose_value,
    ):
        raise ValueError("验证码发送过于频繁，请稍后再试")

    code = generate_email_code()

    send_email_code_message(
        recipient_email=email,
        code=code,
        expires_in=EMAIL_CODE_EXPIRES_IN,
    )

    save_email_code(
        email=email,
        purpose=purpose_value,
        code=code,
        expires_in=EMAIL_CODE_EXPIRES_IN,
        cooldown_in=EMAIL_CODE_COOLDOWN_IN,
    )

    return MessageResponse(
        message="验证码已发送"
    )
