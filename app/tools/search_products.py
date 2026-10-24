from langchain_core.tools import tool
from pydantic import BaseModel, Field
import httpx

class Product(BaseModel):
    keyword: str=Field(description="商品关键词如弯剪，牙剪，梳子之类",
                       min_length=1,
                       max_length=100,)
@tool
def search_products(keyword: str)->dict:
    """
    根据关键词查询商城已上架商品
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
            "note": "仅返回第一页最多5款；价格为起售价，库存和具体规格需另查详情。",
        }

    except httpx.TimeoutException:
        return {"status": "timeout", "products": []}
    except httpx.HTTPError:
        return {"status": "query_failed", "products": []}
    except ValueError:
        return {"status": "invalid_response", "products": []}

