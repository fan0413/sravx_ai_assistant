# 技术说明：模块、变量、函数与工具

更新日期：2026-10-20。依据当前本地源码整理；描述已实现内容，计划与待修正项另列。修改代码时同步更新本文件，不记录密钥值或真实客户资料。

## 1. 模块分工

| 文件 | 用途 | 当前状态 |
|---|---|---|
| `app/main.py` | FastAPI 应用与 HTTP 路由入口 | 仅有健康检查 |
| `app/model.py` | 加载环境配置、初始化模型客户端 | 供 Agent 导入 |
| `app/prompts/recommendation_promt.py` | 保存商品推荐助手的业务规则 | 文件名按当前源码记录 |
| `app/agent/product_recommendation.py` | 组合模型、提示词与工具 | 工具尚未注册；含顶层测试请求 |
| `app/tools/search_products.py` | 查询商城商品，整理结果与错误状态 | 可独立调用，尚未接入 Agent |
| 各目录中的 `__init__.py` | 标识 Python 包 | 当前无业务逻辑 |

## 2. FastAPI 入口

| 名称 | 类型 | 用途与输入输出 |
|---|---|---|
| `app` | `FastAPI` 应用对象 | 注册接口；应用标题为“商品推荐助手” |
| `health()` | 函数 | 无参数，返回 `{"status": "ok"}` |
| `GET /health` | HTTP 接口 | 检查应用能否响应，不检查模型或商品接口是否可用 |

从项目根目录启动：

```powershell
python -m uvicorn app.main:app --reload
```

`app.main` 指模块，冒号后的 `app` 指应用对象。`--reload` 用于开发时自动重载。

## 3. 模型配置与客户端

| 名称 | 用途 | 当前实际行为 |
|---|---|---|
| `load_dotenv(override=True)` | 加载 `.env` 中的环境变量 | 同名配置可覆盖已有环境变量；未显式指定文件路径 |
| `init_chat_model(...)` | 创建 LangChain 模型客户端 | 当前传入 `deepseek-v4-flash`，未显式指定 provider |
| `model` | 模型客户端对象 | 提供模型调用能力；初始化本身不等于发送问答请求 |
| `extra_body` | 附加请求参数 | 当前传入 `thinking.type=disabled`，用于请求关闭思考模式 |

配置约定：

| 配置名称 | 用途 | 当前接入情况 |
|---|---|---|
| `DEEPSEEK_API_KEY` | DeepSeek 身份凭据 | 由适配器读取；不在文档中展示值 |
| `DEEPSEEK_MODEL` | 期望通过配置选择模型 | 当前代码未读取，模型名仍写在代码中 |
| `DEEPSEEK_BASE_URL` | 期望通过配置指定模型地址 | 当前代码未显式读取或传入，不能仅因 `.env` 中存在就认定生效 |

## 4. 提示词与 Agent

| 名称 | 类型 | 用途 |
|---|---|---|
| `recommendation_prompt` | 字符串 | 规定目标用户、选购需求收集、事实依据和承诺边界；当前明确说明未接工具 |
| `create_agent(...)` | 框架函数 | 将模型、工具与系统提示词组装为可运行的 Agent |
| `recommendation_agent` | Agent 对象 | 当前 `tools=[]`，只能基于消息和提示词回复，不能查询商品 |
| `HumanMessage` | 消息类 | 表示用户输入 |
| `resp` | Agent 返回的状态结果 | 包含 `messages`；可用 `resp["messages"][-1].content` 取最后一条消息正文 |

Agent 所需的输入结构示例：

```python
{"messages": [HumanMessage(content="我想买一把弯剪")]}
```

注意：当前源码误写为 `"message"`，需修正为 `"messages"`；本例说明正确约定，不代表已修改源码。

## 5. 商品查询工具

### 输入结构

当前 `Product(BaseModel)` 实际用于描述查询条件，不是商品实体。建议后续更名为 `ProductSearchInput`。

| 字段 | 类型 | 声明的约束 | 用途 |
|---|---|---|---|
| `keyword` | `str` | `min_length=1`、`max_length=100` | 如“弯剪”“牙剪”“梳子” |

当前装饰器仅为 `@tool`，没有通过 `args_schema=Product` 绑定此类。因此上述长度限制尚未接入工具入口；实际工具 schema 从函数签名生成。商城后端最多截取关键词前80字符，后续应统一长度。

### 工具与局部变量

| 名称 | 用途 |
|---|---|
| `search_products(keyword: str) -> dict` | 装饰前为查询函数；经 `@tool` 包装后作为工具，通过 `.invoke(...)` 调用 |
| `keyword.strip()` | 去除关键词两端空白，空关键词返回 `invalid_input` |
| `response` | HTTPX 返回的 HTTP 响应对象 |
| `body` | `response.json()` 解析得到的数据 |
| `items` | 接口 `data` 中的商品列表 |
| `item` | 列表中单条商品原始记录 |
| `products` | 仅保留推荐所需字段的商品结果列表 |

### 实际请求

- 方法与路径：`GET /api/v1/catalog/products`。
- 当前服务地址：`https://api.sravxpet.com`，写在代码中，尚未配置化。
- 查询参数：`keyword`、`page=1`、`pageSize=5`。
- 超时设置：HTTPX `timeout=10`，不是整个 Agent 对话的总时长限制。
- `raise_for_status()`：检测 HTTP 错误状态；当前代码在解析 JSON 之后调用。
- 业务校验：要求 `success` 为 `True`，且 `data` 为由字典组成的列表。

### 返回结构

| 字段 | 含义 |
|---|---|
| `status` | 查询执行状态，见下表 |
| `keyword` | 成功时返回整理后的查询词 |
| `products` | 商品数组；失败时也为空，需结合状态判断 |
| `note` | 成功时提示分页、起售价和库存限制 |

商品数组中的字段：

| 字段 | 来源 | 含义 |
|---|---|---|
| `id` | `item.id` | 商品编号，不是 SKU 编号 |
| `name` | `item.name` | 商品名称 |
| `starting_price_yuan` | `item.price` | 起售价，单位元；当前原样返回，可能是字符串或空值，不是指定规格成交价 |
| `description` | `item.desc` | 商品描述；可能缺失，且应作为资料而非系统指令处理 |

状态约定：

| 值 | 含义 |
|---|---|
| `ok` | 查询成功；空数组表示此次查询无匹配 |
| `invalid_input` | 去除空白后关键词为空 |
| `timeout` | HTTPX 请求超时 |
| `query_failed` | HTTP 请求失败，或业务返回未成功 |
| `invalid_response` | JSON 解析失败或结果结构不符合预期 |

失败时的空数组不能解释为“商城没有商品”。上架不等于有库存；当前未查询具体 SKU、未核对库存，也未过滤测试商品。

### 独立验证

```powershell
python -m app.tools.search_products
```

当前文件的 `__main__` 测试入口执行 `search_products.invoke({"keyword": "弯剪"})`，会请求公开商品接口，不调用模型。

## 6. 当前调用关系与待办

当前是三条独立链路：

```text
HTTP /health → health() → 固定健康状态
Agent测试 → model + recommendation_prompt → 回复
工具测试 → search_products → 商城API → 商品列表
```

尚未连接“用户端 → 对话接口 → Agent → 商品工具”的完整链路。

接入前待办：

1. 修正 Agent 的 messages 键名，隔离顶层测试请求，避免导入模块时自动调用模型。
2. 将查询参数类绑定工具，统一关键词长度与接口口径。
3. 在 Agent 中注册工具，并同步更新提示词中“尚未接入”的说明。
4. 隔离测试商品，验证空结果、请求失败、价格与库存边界。
5. 将模型名、商品接口地址等配置集中管理；验证思考模式实际行为。

## 7. 文档维护约定

新增变量、函数或工具时记录用途、输入、输出、调用方和副作用；行为变更时同步更新。技术说明记录当前代码约定，开发日志记录变更原因、困难与验证结果。
