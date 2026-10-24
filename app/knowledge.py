from langchain_postgres import PGVectorStore

from app.embedding import create_embedding_model
from app.setup_knowledge import create_knowledge_engine,engine


def creat_knowledge_store():
    return PGVectorStore.create_sync(
        engine=engine,
        table_name="knowledge_chunks",
        embedding_model=create_embedding_model(),
    )