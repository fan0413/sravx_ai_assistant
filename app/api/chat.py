from fastapi import APIRouter,Request
from langchain.messages import *

from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()
@router.post("/chat",response_model=ChatResponse)
def chat(request: ChatRequest,http_request:Request)->ChatResponse:
    recommendation_agent=http_request.app.state.recommendation_agent
    config={
        "configurable":{
            "thread_id":request.session_id
        }
    }
    result=recommendation_agent.invoke(
        {
            "messages":[
                HumanMessage(content=request.message)
            ]
        },
        config=config,
    )
    return ChatResponse(
        reply=result["messages"][-1].content,
    )