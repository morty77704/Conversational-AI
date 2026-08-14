from pydantic import ValidationError

from users.entity.user_entity import (
    EmailCodeLoginRequest,
    EmailCodePurpose,
    RegisterRequest,
    SendEmailCodeRequest,
)


send_request = SendEmailCodeRequest(
    email="  TEST@example.com  ",
    purpose="register",
)

assert send_request.email == "test@example.com"
assert send_request.purpose == EmailCodePurpose.REGISTER


login_request = EmailCodeLoginRequest(
    email="TEST@example.com",
    email_code="123456",
)

assert login_request.email == "test@example.com"
assert login_request.email_code == "123456"


register_request = RegisterRequest(
    username="测试用户",
    email="test@example.com",
    password="password123",
    confirm_password="password123",
    email_code="654321",
)

assert register_request.email_code == "654321"


invalid_cases = [
    {
        "email": "test@example.com",
        "purpose": "reset_password",
    },
    {
        "email": "test@example.com",
        "email_code": "1234",
    },
    {
        "email": "test@example.com",
        "email_code": "abcdef",
    },
]

for case in invalid_cases:
    try:
        if "purpose" in case:
            SendEmailCodeRequest(**case)
        else:
            EmailCodeLoginRequest(**case)

        assert False, f"无效参数应该校验失败：{case}"
    except ValidationError:
        pass


print("邮箱验证码 Entity 测试通过")