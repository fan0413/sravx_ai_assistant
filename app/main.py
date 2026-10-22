from anyio.lowlevel import checkpoint
from fastapi import FastAPI
from app.api.chat import router as chat_router
from contextlib import asynccontextmanager
from app.database import create_connection_pool
from langgraph.checkpoint.postgres import PostgresSaver
from app.agent.product_recommendation import create_recommendation_agent

@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = create_connection_pool()
    try:
        pool.open()
        pool.wait(timeout=10)
        app.state.db_pool = pool
        checkpointer = PostgresSaver(pool)
        app.state.recommendation_agent = create_recommendation_agent(checkpointer)

        yield

    finally:
        pool.close()

app = FastAPI(title="商品助手",lifespan=lifespan)
app.include_router(chat_router, prefix="/api")
