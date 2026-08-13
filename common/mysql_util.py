import pymysql
from pymysql.connections import Connection
from pymysql.cursors import DictCursor

from common.config import get_settings


def get_mysql_connection() -> Connection:
    settings = get_settings()

    if not settings.mysql_user.strip():
        raise ValueError("MYSQL_USER 未配置")

    if not settings.mysql_database.strip():
        raise ValueError("MYSQL_DATABASE 未配置")

    return pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_database,
        charset=settings.mysql_charset,
        cursorclass=DictCursor,
        autocommit=False,
        connect_timeout=settings.mysql_connect_timeout,
    )