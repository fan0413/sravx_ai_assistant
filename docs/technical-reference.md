# 技术说明：模块、变量、函数与工具

更新日期：2026-10-22。依据当前本地源码整理；描述已实现内容，计划与待修正项另列。修改代码时同步更新本文件，不记录密钥值或真实客户资料。

## 1. 模块分工

| 文件 | 用途 | 当前状态 |
|---|---|---|
| `app/main.py` | FastAPI 应用与 HTTP 路由入口 | 注册对话路由并管理连接池与数据库版 Agent |
| `app/model.py` | 加载环境配置、初始化模型客户端 | 供 Agent 导入 |
| `app/prompts/recommendation_promt.py` | 保存商品推荐助手的业务规则 | 文件名按当前源码记录 |
| `app/agent/product_recommendation.py` | 组合模型、提示词与工具 | 工厂函数创建 Agent；终端交互已隔离 |
| `app/tools/search_products.py` | 查询商城商品，整理结果与错误状态 | 可独立调用，已注册到 Agent |
| 各目录中的 `__init__.py` | 标识 Python 包 | 当前无业务逻辑 |

## 2. HTTP 对话接口与生命周期

- app：FastAPI 应用对象，当前标题为“商品助手”；注册 /api 路由前缀，当前未定义根路径及 /health。
- POST /api/chat：ChatRequest 接收 message、session_id；ChatResponse 返回 reply。当前字段为字符串，尚未声明长度限制。
- chat(request, http_request)：从 http_request.app.state.recommendation_agent 获取 Agent，将新增 HumanMessage 和 thread_id 配置传给 invoke()，提取最后一条消息正文。
- Request：FastAPI 请求对象，用来访问应用状态，不是用户提交的数据结构。
- lifespan(app)：启动时 pool.open()、pool.wait(timeout=10)，创建 PostgresSaver(pool) 及 Agent；yield 后处理请求，退出时 finally 关闭池。
- app.state.db_pool：服务持有的连接池；app.state.recommendation_agent：使用数据库检查点的 Agent。

启动命令：`python -m uvicorn app.main:app --reload`。直接运行 main.py 不会启动 Uvicorn；自动重载会重新创建应用资源，但数据库状态可保留。

## 3. 模型配置与客户端

| 名称 | 用途 | 当前实际行为 |
|---|---|---|
| `load_dotenv(dotenv_path=env_path)` | 加载 `.env` 中的环境变量 | 基于 model.py 位置读取 app/.env，默认不覆盖已有环境变量 |
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
| `recommendation_prompt` | 字符串 | 规定目标用户、选购需求收集、事实依据和承诺边界；规则应与实际工具能力保持一致 |
| `create_agent(...)` | 框架函数 | 将模型、工具与系统提示词组装为可运行的 Agent |
| `recommendation_agent` | Agent 对象 | 由创建函数返回；已注册 search_products，保存方式由 checkpointer 参数决定 |
| `HumanMessage` | 消息类 | 表示用户输入 |
| `resp` | Agent 返回的状态结果 | 包含 `messages`；可用 `resp["messages"][-1].content` 取最后一条消息正文 |

Agent 所需的输入结构示例：

```python
{"messages": [HumanMessage(content="我想买一把弯剪")]}
```

HTTP 接口每轮传入新增消息，使用 config.configurable.thread_id 关联检查点历史。

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

## 6. PostgreSQL、检查点与调用关系

| 导入或名称 | 用途 |
|---|---|
| psycopg | PostgreSQL 驱动，执行连接与 SQL |
| psycopg.rows.dict_row | 驱动内部行格式工厂，使查询结果按字段名读取 |
| psycopg_pool.ConnectionPool | 独立连接池包的类，复用数据库连接 |
| PostgresSaver | LangGraph PostgreSQL 检查点实现，保存和恢复会话状态 |
| asynccontextmanager | contextlib 标准库装饰器，为 FastAPI 提供生命周期上下文 |
| check_connection() | 只读查询当前账号和数据库，验证基本连接 |
| create_connection_pool() | 创建尚未打开的同步池，最少1个、最多5个连接 |
| setup_checkpoints() | 在 app/seup_checkpoints.py 中执行 setup()，创建表及运行组件迁移，不放在聊天请求中执行 |
| create_recommendation_agent(checkpointer) | 创建并返回使用指定保存器的 Agent；不是发送消息的函数 |

连接池使用空 conninfo，读取本地环境中的 PGHOST、PGPORT、PGDATABASE、PGUSER、PGPASSWORD。SSH 开发连接使用本地127.0.0.1:15432转发到服务器 PostgreSQL；隧道需另行保持运行，DataGrip 的连接不自动供 Python 使用。凭据与私钥不写入本文。

池配置：open=False，kwargs 包含 autocommit=True、row_factory=dict_row、connect_timeout=10。autocommit 用于提交写入及迁移，dict_row 满足保存器按列名读取要求。当前泛型标注未明确字典行类型，编辑器可能提示不匹配。

| 表 | 用途 |
|---|---|
| checkpoints | 会话检查点快照与元数据 |
| checkpoint_blobs | 快照引用的通道数据内容 |
| checkpoint_writes | 执行过程的中间写入 |
| checkpoint_migrations | 表结构迁移版本 |

运行链路：

```text
启动 → 连接池就绪 → PostgresSaver → 创建Agent → app.state
POST /api/chat → 获取Agent → 新增消息与thread_id → 模型/商品工具
                                              ↕
                                       PostgreSQL检查点
关闭 → 释放连接池
```

HTTP 使用数据库记忆；终端 __main__ 入口使用 InMemorySaver，当前缺少调用时的 thread_id 配置，仍需补齐。旧内存历史不会自动迁移进 PostgreSQL。

验证：依据用户重启确认与截图，同一会话恢复测试编号和选购条件；两个已有会话表现符合各自历史。全新会话隔离、用户身份授权和并发正确性未完成验证。

待办：绑定工具输入 schema 并统一长度；完善输入、异常与超时控制；区分测试商品；规范配置与类型标注；补会话归属、历史保留及备份。未来 RAG 可另行扩展，不将检查点表当向量知识库。

## 7. 文档维护约定

新增变量、函数或工具时记录用途、输入、输出、调用方和副作用；行为变更时同步更新。技术说明记录当前代码约定，开发日志记录变更原因、困难与验证结果。
