from unittest.mock import patch
from pymysql.err import IntegrityError
from common.password_util import verify_password
from users.entity.user_entity import RegisterRequest
from users.service.user_service import register_user


request = RegisterRequest(
    username="测试用户",
    email="TEST@example.com",
    password="test-password-123",
    confirm_password="test-password-123",
)


with (
    patch(
        "users.service.user_service.email_exists",
        return_value=False,
    ),
    patch(
        "users.service.user_service.create_user",
        return_value={
            "id": 1,
            "username": "测试用户",
            "email": "test@example.com",
            "status": 1,
        },
    ) as create_user_mock,
):
    result = register_user(request)

    create_arguments = create_user_mock.call_args.kwargs
    saved_hash = create_arguments["password_hash"]

    assert result.id == 1
    assert result.email == "test@example.com"
    assert saved_hash != request.password
    assert verify_password(request.password, saved_hash)
    assert "password_hash" not in result.model_dump()

    print("正常注册测试通过")

# 情况一：预检查已经发现邮箱存在
with (
    patch(
        "users.service.user_service.email_exists",
        return_value=True,
    ),
    patch(
        "users.service.user_service.create_user",
    ) as create_user_mock,
):
    try:
        register_user(request)
        assert False, "邮箱重复时应该抛出异常"
    except ValueError as error:
        assert str(error) == "邮箱已注册"

    assert not create_user_mock.called
    print("邮箱预检查测试通过")


# 情况二：预检查通过，但 INSERT 时发生唯一键冲突
with (
    patch(
        "users.service.user_service.email_exists",
        return_value=False,
    ),
    patch(
        "users.service.user_service.create_user",
        side_effect=IntegrityError(
            1062,
            "Duplicate entry",
        ),
    ),
):
    try:
        register_user(request)
        assert False, "唯一键冲突时应该抛出异常"
    except ValueError as error:
        assert str(error) == "邮箱已注册"

    print("数据库唯一键冲突测试通过")