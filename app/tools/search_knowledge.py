from langchain_core.tools import tool
from langchain_postgres import PGVectorStore

def create_search_knowledge_tool(store: PGVectorStore,):
    @tool
    def search_knowledge(query:str):
        """
        检索已入库的SRAVX宠物美容剪刀知识。

        适用于系列定位、钢材、剪型、尺寸、左右手、颜色、结构及已收录的使用风险说明。不查询实时商品价格、库存、订单或物流。

        query应表达客户需要核实的具体知识点，保留必要品牌名、材料名或剪型；不要加入与问题无关的条件。


        结果是相关候选资料，不保证包含完整答案；章节可能为空。
        仅依据正文支持的内容回答。无结果或缺少关键依据时，不得自行补造品牌结论。

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

