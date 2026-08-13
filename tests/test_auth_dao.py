from unittest.mock import MagicMock, patch

from users.dao.auth_dao import (
    delete_access_token,
    get_token_user_id,
    save_access_token,
)


redis_mock = MagicMock()


with patch(
    "users.dao.auth_dao.get_redis_client",
    return_value=redis_mock,
):
    save_access_token(
        token_id="test-token-id",
        user_id=1,
        expires_in=1800,
    )

    redis_mock.set.assert_called_once_with(
        "auth:access:test-token-id",
        "1",
        ex=1800,
    )

    redis_mock.get.return_value = "1"

    user_id = get_token_user_id(
        "test-token-id"
    )

    assert user_id == "1"
    redis_mock.get.assert_called_once_with(
        "auth:access:test-token-id"
    )

    redis_mock.delete.return_value = 1

    deleted = delete_access_token(
        "test-token-id"
    )

    assert deleted is True
    redis_mock.delete.assert_called_once_with(
        "auth:access:test-token-id"
    )


print("Redis 登录状态 DAO 测试通过")