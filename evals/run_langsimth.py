import asyncio
from collections import Counter
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / "app" / ".env")
from langsmith import Client
from langgraph.checkpoint.memory import InMemorySaver

from app.agent.product_recommendation import create_recommendation_agent
from app.rag.engine import create_knowledge_engine
from app.rag.knowledge import create_knowledge_store
from app.tools.search_knowledge import create_search_knowledge_tool

def main():
    client = Client()
    engine=create_knowledge_engine()
    try:
        store=knowledge_store=create_knowledge_store(engine)
        knowledge_tool=create_search_knowledge_tool(store)
        agent=create_recommendation_agent(
            checkpointer=InMemorySaver(),
            knowledge_tool=knowledge_tool,
        )
        def predict(inputs: dict) -> dict:
            """运行一条用例，返回回复和工具请求记录。"""
            messages = inputs["messages"]

            if not messages:
                raise ValueError("评测用例的 messages 不能为空")

            session_id = f"eval_{uuid4().hex}"
            replies = []
            tool_calls = []

            # 第一阶段：按顺序完成该用例的所有对话。
            for user_message in messages:
                result = agent.invoke(
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": user_message,
                            }
                        ]
                    },
                    config={
                        "configurable": {
                            "thread_id": session_id,
                        },
                        "recursion_limit": 12,
                    },
                )

                replies.append(
                    result["messages"][-1].content
                )

            # 第二阶段：从最终累积的消息中提取工具请求。
            for message in result["messages"]:
                for call in getattr(message, "tool_calls", []):
                    tool_calls.append({
                        "name": call["name"],
                        "args": call["args"],
                    })

            # 第三阶段：所有处理完成后，统一返回结果。
            return {
                "reply": replies[-1],
                "replies": replies,
                "tool_calls": tool_calls,
            }

        # 自动读取云端数据集全部用例，编号来自导入时的 Metadata.id。
        examples = list(client.list_examples(
            dataset_name="cases-customer-v1"
        ))
        if not examples:
            raise ValueError("云端评测数据集为空，请先导入用例")

        found_ids = [
            (example.metadata or {}).get("id")
            for example in examples
        ]
        if any(not isinstance(case_id, str) or not case_id.strip()
               for case_id in found_ids):
            raise ValueError("部分用例缺少有效编号，请检查云端 Metadata.id")
        duplicates = [case_id for case_id, count in Counter(found_ids).items()
                      if count > 1]
        if duplicates:
            raise ValueError(
                f"云端用例编号重复，请先清理重复导入：{duplicates}"
            )
        for example in examples:
            messages = (example.inputs or {}).get("messages")
            if (not isinstance(messages, list) or not messages
                    or any(not isinstance(message, str) or not message.strip()
                           for message in messages)):
                raise ValueError(
                    f"用例 {example.metadata['id']} 的 Inputs.messages "
                    "必须是非空字符串列表，请检查导入字段映射"
                )
        print(f"本次评测共 {len(examples)} 题，编号：{', '.join(found_ids)}")

        client.evaluate(
            predict,
            data=examples,
            experiment_prefix="cases-customer-v1",
            description="云端全部知识用例：自动读取编号，人工评分",
            max_concurrency=1,
            num_repetitions=1,
        )
    finally:
        asyncio.run(engine.close())


if __name__ == "__main__":
    main()

