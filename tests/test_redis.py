from common.redis_util import get_redis_client


client = get_redis_client()

assert client.ping() is True
assert get_redis_client() is client

print("Redis 连接成功")
print("Redis 客户端已缓存")