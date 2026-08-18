from functools import lru_cache

from redis import Redis

from common.config import get_settings


# 使用装饰器作用是把函数的返回结果缓存起来，从而让后续调用复用同一个对象，而不是重新创建。
@lru_cache
def get_redis_client() -> Redis:
    settings = get_settings()

    return Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        password=settings.redis_password or None,
        decode_responses=True,
        socket_connect_timeout=settings.redis_connect_timeout,
        socket_timeout=settings.redis_socket_timeout,
        protocol=2,  # 新版 Python 客户端使用旧版 RESP2 通信协议，以兼容 Redis 3.0。
    )