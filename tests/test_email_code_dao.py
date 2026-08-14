from unittest.mock import MagicMock, patch


from users.dao.email_code_dao import (
    delete_email_code_state,
    email_code_in_cooldown,
    get_email_code,
    get_email_code_attempts,
    increment_email_code_attempts,
    save_email_code,
)


client = MagicMock()
pipeline = MagicMock()
client.pipeline.return_value = pipeline


with patch(
    "users.dao.email_code_dao.get_redis_client",
    return_value=client,
):
    save_email_code(
        email="  TEST@example.com  ",
        purpose="register",
        code="123456",
        expires_in=300,
        cooldown_in=60,
    )


client.pipeline.assert_called_once_with(
    transaction=True
)
pipeline.delete.assert_called_once_with(
    (
        "auth:email_code_attempts:"
        "register:test@example.com"
    )
)

assert pipeline.set.call_count == 2

code_call = pipeline.set.call_args_list[0]
assert code_call.args == (
    "auth:email_code:register:test@example.com",
    "123456",
)
assert code_call.kwargs == {
    "ex": 300,
}

cooldown_call = pipeline.set.call_args_list[1]
assert cooldown_call.args == (
    (
        "auth:email_code_cooldown:"
        "register:test@example.com"
    ),
    "1",
)
assert cooldown_call.kwargs == {
    "ex": 60,
}

pipeline.execute.assert_called_once_with()


cooldown_client = MagicMock()
cooldown_client.exists.return_value = 1

with patch(
    "users.dao.email_code_dao.get_redis_client",
    return_value=cooldown_client,
):
    in_cooldown = email_code_in_cooldown(
        email="TEST@example.com",
        purpose="login",
    )


assert in_cooldown is True

cooldown_client.exists.assert_called_once_with(
    (
        "auth:email_code_cooldown:"
        "login:test@example.com"
    )
)
read_client = MagicMock()
read_client.get.return_value = "123456"

with patch(
    "users.dao.email_code_dao.get_redis_client",
    return_value=read_client,
):
    code = get_email_code(
        email="TEST@example.com",
        purpose="register",
    )

assert code == "123456"
read_client.get.assert_called_once_with(
    "auth:email_code:register:test@example.com"
)


attempts_client = MagicMock()
attempts_client.get.return_value = "2"

with patch(
    "users.dao.email_code_dao.get_redis_client",
    return_value=attempts_client,
):
    attempts = get_email_code_attempts(
        email="test@example.com",
        purpose="login",
    )

assert attempts == 2


increment_client = MagicMock()
increment_pipeline = MagicMock()
increment_client.pipeline.return_value = (
    increment_pipeline
)
increment_pipeline.execute.return_value = [3, True]

with patch(
    "users.dao.email_code_dao.get_redis_client",
    return_value=increment_client,
):
    attempts = increment_email_code_attempts(
        email="test@example.com",
        purpose="login",
        expires_in=300,
    )

assert attempts == 3
increment_pipeline.incr.assert_called_once_with(
    "auth:email_code_attempts:login:test@example.com"
)
increment_pipeline.expire.assert_called_once_with(
    "auth:email_code_attempts:login:test@example.com",
    300,
)
increment_pipeline.execute.assert_called_once_with()


delete_client = MagicMock()
delete_client.delete.return_value = 2

with patch(
    "users.dao.email_code_dao.get_redis_client",
    return_value=delete_client,
):
    deleted = delete_email_code_state(
        email="test@example.com",
        purpose="register",
    )

assert deleted is True
delete_client.delete.assert_called_once_with(
    "auth:email_code:register:test@example.com",
    (
        "auth:email_code_attempts:"
        "register:test@example.com"
    ),
)


empty_attempts_client = MagicMock()
empty_attempts_client.get.return_value = None

with patch(
    "users.dao.email_code_dao.get_redis_client",
    return_value=empty_attempts_client,
):
    attempts = get_email_code_attempts(
        email="test@example.com",
        purpose="register",
    )

assert attempts == 0


print("邮箱验证码 Redis DAO 测试通过")
