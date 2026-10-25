from langchain_core.tools import tool
from langchain_postgres import PGVectorStore

def create_search_knowledge_tool(store: PGVectorStore,):
    @tool
    def search_knowledge(query:str):
        """
        检索宠物美容剪刀工具，不用于查询实时商品价格，库存订单等

        """

        documents=store.similarity_search(query,k=3)
        return {
            "results":[
                {
                    "content": document.page_content,
                    "source": document.metadata.get("source", ""),
                    "section": document.metadata.get("三级标题", "")
                }
                for document in documents
            ]
        }
    return search_knowledge

