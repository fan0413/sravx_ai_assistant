from fastapi import APIRouter,Request,HTTPException
from langchain.messages import *
from openai import APITimeoutError
from langgraph.errors import GraphRecursionError
from app.schemas.chat import ChatRequest, ChatResponse
from psycopg import OperationalError, InterfaceError
from psycopg_pool import PoolTimeout
router = APIRouter()
@router.post("/chat",response_model=ChatResponse)
def chat(request: ChatRequest,http_request:Request)->ChatResponse:
    recommendation_agent=http_request.app.state.recommendation_agent
    config={
        "configurable":{
            "thread_id":request.session_id
        },
        "recursion_limit":12
    }
    try:
        result=recommendation_agent.invoke(
            {
                "messages":[
                    HumanMessage(content=request.message)
                ]
            },
            config=config,
        )
    except APITimeoutError as error:
        raise HTTPException(
            status_code=504,
            detail="模型响应超时",
        )from error

    except(OperationalError,InterfaceError,PoolTimeout) as error:
        raise HTTPException(
            status_code=503,
            detail="会话存储暂不可用",
        )from error
    except GraphRecursionError as error:
        raise HTTPException(
            status_code=503,
            detail="本次处理步骤过多，请缩小查询范围后重试"
        )

    return ChatResponse(
        reply=result["messages"][-1].content,
    )