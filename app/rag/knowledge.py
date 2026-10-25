from langchain_postgres import PGVectorStore

from app.rag.embedding import create_embedding_model



def create_knowledge_store(engine):
    return PGVectorStore.create_sync(
        engine=engine,
        table_name="knowledge_chunks",
        embedding_service=create_embedding_model(),
    )