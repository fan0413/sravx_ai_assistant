from langchain.agents import create_agent
from app.model import model
from app.prompts.recommendation_promt import recommendation_prompt
from langchain.messages import *
recommendation_agent=create_agent(
    name=" product_recommendation",
    model=model,
    system_prompt=recommendation_prompt,
    tools=[]
)

resp=recommendation_agent.invoke(
    {
        "message":[
            HumanMessage("你好我想买一把剪刀")
        ]
    }
)
print(resp)