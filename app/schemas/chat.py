from pydantic import BaseModel,Field,ConfigDict



class ChatRequest(BaseModel):
    message: str=Field(description="会话消息",min_length=1,max_length=1000)
    session_id:str=Field(description="会话id",min_length=1,max_length=100)
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )


class ChatResponse(BaseModel):
    reply:str=Field(description="回复")