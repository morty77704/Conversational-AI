from typing import Any

from pymysql.err import IntegrityError

from common.jwt_util import create_access_token
from common.password_util import (
    hash_password,
    verify_password,
)
from users.dao.auth_dao import save_access_token
from users.dao.user_dao import (
    create_user,
    email_exists,
    get_user_auth_by_email,
)
from users.entity.user_entity import (
    EmailCodeLoginRequest,
    EmailCodePurpose,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UserResponse,
    validate_password_confirmation,
)
from users.service.email_code_service import (
    verify_email_code,
)


def _create_login_response(
    user: dict[str, Any],
) -> LoginResponse:
    """
    为已经完成身份验证的用户创建登录状态。

    密码登录和邮箱验证码登录只负责验证身份；
    JWT 创建、Redis 保存和响应构造统一放在这里。
    """
    token_result = create_access_token(
        user["id"]
    )

    save_access_token(
        token_id=token_result["token_id"],
        user_id=user["id"],
        expires_in=token_result["expires_in"],
    )

    return LoginResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        access_token=token_result["access_token"],
        token_type="Bearer",
        expires_in=token_result["expires_in"],
    )


def register_user(
    request: RegisterRequest,
) -> UserResponse:
    validate_password_confirmation(request)

    if email_exists(request.email):
        raise ValueError("邮箱已注册")

    verify_email_code(
        email=str(request.email),
        purpose=EmailCodePurpose.REGISTER,
        submitted_code=request.email_code,
    )

    password_hash = hash_password(
        request.password
    )

    try:
        user = create_user(
            username=request.username,
            email=request.email,
            password_hash=password_hash,
        )
    except IntegrityError as error:
        if error.args and error.args[0] == 1062:
            raise ValueError(
                "邮箱已注册"
            ) from error
        raise

    return UserResponse.model_validate(user)


def login_user(
    request: LoginRequest,
) -> LoginResponse:
    """
    邮箱密码登录。
    """
    user = get_user_auth_by_email(
        str(request.email)
    )

    if user is None:
        raise ValueError("邮箱或密码错误")

    if not verify_password(
        request.password,
        user["password_hash"],
    ):
        raise ValueError("邮箱或密码错误")

    if user["status"] != 1:
        raise ValueError("账号已禁用")

    return _create_login_response(user)


def login_user_by_email_code(
    request: EmailCodeLoginRequest,
) -> LoginResponse:
    """
    邮箱验证码登录。
    """
    user = get_user_auth_by_email(
        str(request.email)
    )

    if user is None:
        raise ValueError("邮箱账号不存在")

    if user["status"] != 1:
        raise ValueError("账号已禁用")

    verify_email_code(
        email=str(request.email),
        purpose=EmailCodePurpose.LOGIN,
        submitted_code=request.email_code,
    )

    return _create_login_response(user)