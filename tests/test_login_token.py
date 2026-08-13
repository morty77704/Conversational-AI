from unittest.mock import patch

from users.entity.user_entity import LoginRequest
from users.service.user_service import login_user


request = LoginRequest(
    email="test@example.com",
    password="test-password-123",
)

user = {
    "id": 1,
    "username": "测试用户",
    "email": "test@example.com",
    "password_hash": "$2b$12$mock",
    "status": 1,
}

token_result = {
    "access_token": "mock-access-token",
    "token_id": "mock-token-id",
    "expires_in": 1800,
}


with (
    patch(
        "users.service.user_service.get_user_auth_by_email",
        return_value=user,
    ),
    patch(
        "users.service.user_service.verify_password",
        return_value=True,
    ),
    patch(
        "users.service.user_service.create_access_token",
        return_value=token_result,
    ) as create_token_mock,
    patch(
        "users.service.user_service.save_access_token",
    ) as save_token_mock,
):
    result = login_user(request)

    create_token_mock.assert_called_once_with(1)

    save_token_mock.assert_called_once_with(
        token_id="mock-token-id",
        user_id=1,
        expires_in=1800,
    )

    assert result.id == 1
    assert result.access_token == "mock-access-token"
    assert result.token_type == "Bearer"
    assert result.expires_in == 1800
    assert "password_hash" not in result.model_dump()

    print("登录签发 JWT 测试通过")