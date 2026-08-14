from common.password_util import (
    hash_password,
    verify_password,
)
from users.entity.user_entity import (
    RegisterRequest,
    validate_password_confirmation,
)


request = RegisterRequest(
    username="测试用户",
    email="TEST@example.com",
    password="test-password-123",
    confirm_password="test-password-123",
    email_code="123456",
)

validate_password_confirmation(request)

password_hash = hash_password(request.password)

assert request.email == "test@example.com"
assert password_hash != request.password
assert verify_password(request.password, password_hash)
assert not verify_password("wrong-password", password_hash)


print("密码哈希与确认测试通过")
