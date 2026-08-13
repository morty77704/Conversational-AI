from common.mysql_util import get_mysql_connection


connection = get_mysql_connection()

try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 AS value")
        result = cursor.fetchone()
        print(result)
finally:
    connection.close()