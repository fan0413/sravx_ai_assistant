from fastapi import FastAPI
from app.api.chat import router as chat_router




app = FastAPI(title="商品助手")
app.include_router(chat_router, prefix="/api")