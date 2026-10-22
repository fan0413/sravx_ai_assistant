from pathlib import Path
import psycopg
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)
from psycopg.rows import dict_row
from psycopg_pool import  ConnectionPool

#检查初始化链接测试
def check_connection():
    with psycopg.connect(connect_timeout=10) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_user, current_database()")
            user,database=cursor.fetchone()
            print(f"Connected to {user}:{database}")


def create_connection_pool()->ConnectionPool:
    return ConnectionPool(
        conninfo="",
        min_size=1,
        max_size=5,
        open=False,
        kwargs={
            "autocommit": True,
            "row_factory": dict_row,
            "connect_timeout": 10,
        }
    )