from pydantic import BaseModel,Field

class ChatRequest(BaseModel):
    message: str=Field(description="会话消息")
    session_id:str=Field(description="会话id")

class ChatResponse(BaseModel):
    reply:str=Field(description="回复")