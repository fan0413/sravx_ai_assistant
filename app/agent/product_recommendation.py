from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver


from app.model import model
from app.prompts.recommendation_promt import recommendation_prompt
from langchain.messages import *
import app.tools
from app.tools import search_products
from rich import print as rprint
def create_recommendation_agent(checkpointer,knowledge_tool=None):
    tools = [search_products.search_products]
    if knowledge_tool is not None:
        tools.append(knowledge_tool)

    return create_agent(
        name=" product_recommendation",
        model=model,
        system_prompt=recommendation_prompt,
         tools=tools,
        checkpointer=checkpointer,
)


if __name__ == "__main__":
    recommendation_agent = create_recommendation_agent(InMemorySaver())
    while True:
        user_input = input("你：").strip()
        if user_input == "exit":
            break
        else:
            resp = recommendation_agent.invoke(
                {
                    "messages": [
                        HumanMessage(content=user_input)
                    ]
                },
            )
        rprint(resp["messages"][-1].content)
