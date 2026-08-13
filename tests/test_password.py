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
)

validate_password_confirmation(request)

password_hash = hash_password(request.password)

print(request.email)
print(password_hash != request.password)
print(verify_password(request.password, password_hash))
print(verify_password("wrong-password", password_hash))