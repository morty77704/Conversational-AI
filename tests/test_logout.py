from unittest.mock import patch

from users.service.auth_service import logout_user


auth_context = {
    "user": {
        "id": 1,
        "username": "测试用户",
        "email": "test@example.com",
    },
    "token_id": "mock-token-id",
    "payload": {
        "sub": "1",
        "jti": "mock-token-id",
    },
}


with patch(
    "users.service.auth_service.delete_access_token",
    return_value=True,
) as delete_mock:
    result = logout_user(auth_context)

    delete_mock.assert_called_once_with(
        "mock-token-id"
    )

    assert result.message == "退出登录成功"

    print("退出登录 Service 测试通过")