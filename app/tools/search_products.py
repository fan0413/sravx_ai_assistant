from langchain_core.tools import tool
from pydantic import BaseModel, Field
import httpx

class Product(BaseModel):
    keyword: str=Field(description="商品关键词如弯剪，牙剪，梳子之类",
                       min_length=1,
                       max_length=100,)

@tool(args_schema=Product)
def search_products(keyword: str)->dict:
    """
    按关键词查询商城已上架商品，用于具体商品推荐、价格及在售查询。
不用于回答一般钢材、尺寸或剪型知识。

keyword使用简短商品名称或剪型，如“直剪”“弯剪”“鱼骨剪”。
仅在客户已明确提出时加入尺寸或系列，不把整段需求作为关键词。

成功时返回status=ok和products。
商品字段包括id、name、description、starting_price_yuan。
价格单位为元，属于起售价，不代表所选规格的最终成交价。
仅查询第一页，最多返回5款，不代表全店完整商品或销量排名。
字段缺失时不得推断对应参数。

status=ok且products为空，只表示本次未找到匹配商品。
timeout、query_failed、invalid_response表示查询异常，
不能解释为没有商品；invalid_input表示关键词无效。

本工具不能核实库存、物流时效、完整规格或销量排名，
不得据此承诺有货、到货日期或推荐为销量靠前商品
    """

    keyword = keyword.strip()

    if not keyword:
        return {"status": "invalid_input", "products": []}

    try:
        response = httpx.get(
            "https://api.sravxpet.com/api/v1/catalog/products",
            params={"keyword": keyword, "page": 1, "pageSize": 5},
            timeout=10,
        )
        #
        body = response.json()

        response.raise_for_status()
        if not isinstance(body, dict) or body.get("success") is not True:
            return {"status": "query_failed", "products": []}

        items = body.get("data")
        if not isinstance(items, list) or any(
            not isinstance(item, dict) for item in items
        ):
            return {"status": "invalid_response", "products": []}

        products = [
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "starting_price_yuan": item.get("price"),
             "description": item.get("desc"),
            }
            for item in items
        ]

        return {
            "status": "ok",
            "keyword": keyword,
            "products": products,
            "note": "仅返回第一页最多5个。",
        }

    except httpx.TimeoutException:
        return {"status": "timeout", "products": []}
    except httpx.HTTPError:
        return {"status": "query_failed", "products": []}
    except ValueError:
        return {"status": "invalid_response", "products": []}

