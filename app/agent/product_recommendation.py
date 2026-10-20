from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from app.model import model
from app.prompts.recommendation_promt import recommendation_prompt
from langchain.messages import *
import app.tools
from app.tools import search_products
from rich import print as rprint
recommendation_agent=create_agent(
    name=" product_recommendation",
    model=model,
    system_prompt=recommendation_prompt,
    tools=[
        search_products.search_products
    ],
    checkpointer=InMemorySaver()
)
config={
    "configurable":{
        "thread_id":"test01"
    }
}
while True:
    user_input = input()
    if  user_input == "exit":
        break
    else:
        resp = recommendation_agent.invoke(
            {
                "messages": [
                    HumanMessage(content=user_input)
                ]
            },
        config=config
        )
    rprint(resp["messages"][-1].content)
