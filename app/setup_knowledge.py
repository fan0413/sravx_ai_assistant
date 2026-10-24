
import asyncio
import os
from pathlib import Path
import sys
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")
from sqlalchemy import URL
from langchain_postgres import PGEngine

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )
def create_knowledge_engine():
    url=URL.create(
        drivername="postgresql+psycopg",
        username=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        host=os.environ["PGHOST"],
        port=int(os.environ["PGPORT"]),
        database=os.environ["PGDATABASE"],

    )
    return PGEngine.from_connection_string(url=url)


if __name__ == "__main__":
    engine = create_knowledge_engine()

    try:
        engine.init_vectorstore_table(
            table_name="knowledge_chunks",
            vector_size=1024,
        )
        print("知识库表初始化成功")
    finally:
        asyncio.run(engine.close())