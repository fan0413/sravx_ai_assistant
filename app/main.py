from anyio.lowlevel import checkpoint
from fastapi import FastAPI
from app.api.chat import router as chat_router
from contextlib import asynccontextmanager
from app.database import create_connection_pool
from langgraph.checkpoint.postgres import PostgresSaver
from app.agent.product_recommendation import create_recommendation_agent
from app.rag.engine import create_knowledge_engine
from app.rag.knowledge import create_knowledge_store
from app.tools.search_knowledge import create_search_knowledge_tool

@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = create_connection_pool()
    knowledge_engine=None
    try:
        pool.open()
        pool.wait(timeout=10)
        app.state.db_pool = pool
        checkpointer = PostgresSaver(pool)
        knowledge_engine=create_knowledge_engine()
        store=create_knowledge_store(knowledge_engine)
        knowledge_tool=create_search_knowledge_tool(store)
        app.state.recommendation_agent = (
            create_recommendation_agent(
                checkpointer,
                knowledge_tool=knowledge_tool
            )
        )
        yield

    finally:
        try:
            if knowledge_engine is not None:
                await knowledge_engine.close()
        finally:
            pool.close()

app = FastAPI(title="商品助手",lifespan=lifespan)
app.include_router(chat_router, prefix="/api")
