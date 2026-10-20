from fastapi import APIRouter
from langchain.messages import *
from app.agent.product_recommendation import recommendation_agent
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()
@router.post("/chat",response_model=ChatResponse)
def chat(request: ChatRequest)->ChatResponse:
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