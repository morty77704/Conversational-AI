from pymysql.err import IntegrityError

from common.password_util import hash_password, verify_password
from users.dao.user_dao import create_user, email_exists, get_user_auth_by_email
from users.entity.user_entity import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UserResponse,
    validate_password_confirmation,
)
from users.entity.user_entity import LoginRequest
from common.jwt_util import create_access_token
from users.dao.auth_dao import save_access_token


def register_user(request: RegisterRequest) -> UserResponse:
    validate_password_confirmation(request)

    if email_exists(request.email):
        raise ValueError("邮箱已注册")

    password_hash = hash_password(request.password)

    try:
        user = create_user(
            username=request.username,
            email=request.email,
            password_hash=password_hash,
        )
    except IntegrityError as error:
        if error.args and error.args[0] == 1062:
            raise ValueError("邮箱已注册") from error
        raise

    return UserResponse.model_validate(user)


def login_user(request: LoginRequest) -> LoginResponse:
    user = get_user_auth_by_email(request.email)

    if user is None:
        raise ValueError("邮箱或密码错误")

    if not verify_password(
            request.password,
            user["password_hash"],
    ):
        raise ValueError("邮箱或密码错误")

    if user["status"] != 1:
        raise ValueError("账号已禁用")

    token_result = create_access_token(user["id"])

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
