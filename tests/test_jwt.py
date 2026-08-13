from common.jwt_util import (
    create_access_token,
    decode_access_token,
)


token_result = create_access_token(user_id=1)

assert token_result["access_token"]
assert token_result["token_id"]
assert token_result["expires_in"] == 30 * 60

payload = decode_access_token(
    token_result["access_token"]
)

assert payload["sub"] == "1"
assert payload["jti"] == token_result["token_id"]
assert payload["type"] == "access"
assert payload["exp"] > payload["iat"]

print("JWT 生成和解析测试通过")