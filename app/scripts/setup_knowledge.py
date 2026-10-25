
import asyncio
import os
from pathlib import Path
import sys
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent .parent/ ".env")
from sqlalchemy import URL
from langchain_postgres import PGEngine

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )


# if __name__ == "__main__":
#     engine = create_knowledge_engine()
#
#     try:
#         engine.init_vectorstore_table(
#             table_name="knowledge_chunks",
#             vector_size=1024,
#         )
#         print("知识库表初始化成功")
#     finally:
#         asyncio.run(engine.close())