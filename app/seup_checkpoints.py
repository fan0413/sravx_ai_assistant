import psycopg
from dotenv import load_dotenv
from pathlib import Path
from psycopg.rows import dict_row
load_dotenv(Path(__file__).resolve().parent/".env")
from langgraph.checkpoint.postgres import PostgresSaver


def setup_checkpoints():
    with psycopg.connect(row_factory=dict_row
                         ,autocommit=True,
                         ) as conn:
        checkpointer=PostgresSaver(conn)
        checkpointer.setup()
        print("初始化完成")

if __name__=="__main__":
    setup_checkpoints()