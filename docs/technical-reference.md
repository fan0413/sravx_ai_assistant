# 技术说明：模块、变量、函数与工具

更新日期：2026-10-29。依据当前本地源码整理；描述已实现内容，计划与待修正项另列。修改代码时同步更新本文件，不记录密钥值或真实客户资料。

## 1. 模块分工

| 文件 | 用途 | 当前状态 |
|---|---|---|
| `app/main.py` | FastAPI 应用与 HTTP 路由入口 | 注册对话路由并管理连接池与数据库版 Agent |
| `app/model.py` | 加载环境配置、初始化模型客户端 | 供 Agent 导入 |
| `app/prompts/recommendation_promt.py` | 保存商品推荐助手的业务规则 | 文件名按当前源码记录 |
| `app/agent/product_recommendation.py` | 组合模型、提示词与工具 | 工厂函数创建 Agent；终端交互已隔离 |
| `app/tools/search_products.py` | 查询商城商品，整理结果与错误状态 | 可独立调用，已注册到 Agent |
| `app/rag/embedding.py` | 创建向量模型封装 | 独立运行曾返回1024维向量 |
| `app/scripts/setup_knowledge.py` | 调用独立引擎并初始化向量表 | 已建表，不随聊天请求运行 |
| `app/rag/knowledge.py` | 创建向量存储对象 | 已通过embedding_service接入向量模型，供知识工具调用 |
| `knowledge/` | 保存品牌知识与售后知识 Markdown | 剪刀正文已确认34片段入库；售后正文未确认入库 |
| 各目录中的 `__init__.py` | 标识 Python 包 | 当前无业务逻辑 |

## 2. HTTP 对话接口与生命周期

- app：FastAPI 应用对象，当前标题为“商品助手”；注册 /api 路由前缀，当前未定义根路径及 /health。
- POST /api/chat：ChatRequest 接收 message、session_id；ChatResponse 返回 reply。message 为1～1000字符，session_id 为1～100字符，先去除字符串首尾空白。
- chat(request, http_request)：从 http_request.app.state.recommendation_agent 获取 Agent，将新增 HumanMessage 和 thread_id 配置传给 invoke()，提取最后一条消息正文。
- Request：FastAPI 请求对象，用来访问应用状态，不是用户提交的数据结构。
- lifespan(app)：启动时 pool.open()、pool.wait(timeout=10)，创建PostgresSaver(pool)、知识引擎、向量库及知识工具，再创建Agent；yield后处理请求，退出时关闭知识引擎和连接池。
- app.state.db_pool：服务持有的连接池；app.state.recommendation_agent：使用数据库检查点的 Agent。

启动命令：`python -m uvicorn app.main:app --reload`。直接运行 main.py 不会启动 Uvicorn；自动重载会重新创建应用资源，但数据库状态可保留。

## 3. 模型配置与客户端

| 名称 | 用途 | 当前实际行为 |
|---|---|---|
| `load_dotenv(dotenv_path=env_path)` | 加载 `.env` 中的环境变量 | 基于 model.py 位置读取 app/.env，默认不覆盖已有环境变量 |
| `init_chat_model(...)` | 创建 LangChain 模型客户端 | 当前传入 `deepseek-v4-flash`，未显式指定 provider |
| `model` | 模型客户端对象 | 提供模型调用能力；初始化本身不等于发送问答请求 |
| `timeout`、`max_retries` | 网络请求超时与重试 | 当前分别为15秒、最多额外重试2次；不是整次 Agent 请求的总耗时限制 |
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
| `recommendation_agent` | Agent 对象 | 由创建函数返回；已注册 search_products，可传入knowledge_tool注册search_knowledge；保存方式由checkpointer决定 |
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

当前使用 `@tool(args_schema=Product)`，已将Product参数类绑定到工具入口，声明关键词长度为1～100字符。商城后端最多截取前80字符，长度口径仍待统一；纯空白由函数内strip后处理，绑定不代表所有边界已运行验证。

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

当前源码已无 `__main__` 测试入口，直接运行上述命令不会执行商品查询。需要独立验证时，应明确编写调用入口；实际调用工具会请求公开商品接口，不调用模型。

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
| setup_checkpoints() | 在 app/scripts/seup_checkpoints.py 中执行 setup()，创建表及运行组件迁移，不放在聊天请求中执行 |
| create_recommendation_agent(checkpointer, knowledge_tool=None) | 创建并返回使用指定保存器的 Agent；不是发送消息的函数 |

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

验证：完成服务重启并核对响应截图后，确认同一会话恢复测试编号和选购条件；两个已有会话表现符合各自历史。全新会话隔离、用户身份授权和并发正确性未完成验证。

待办：绑定工具输入 schema 并统一长度；进一步验证输入、异常与超时控制；区分测试商品；规范配置与类型标注；补会话归属、历史保留及备份。RAG已单独使用knowledge_chunks，不将检查点表当向量知识库。

## 7. 输入约束与异常响应

| 名称 | 用途与实际设置 |
|---|---|
| ConfigDict | Pydantic 模型配置；ChatRequest.model_config 设置 str_strip_whitespace=True |
| Field | 字段长度校验，message 为1～1000字符，session_id 为1～100字符 |
| HTTPException | FastAPI HTTP 错误响应，指定状态码与 detail |
| APITimeoutError | 底层 openai 兼容客户端的模型请求超时异常，不表示改用其他模型服务商 |
| OperationalError、InterfaceError | psycopg 的数据库运行或接口状态异常 |
| PoolTimeout | psycopg_pool 等待可用连接超时 |
| GraphRecursionError | LangGraph 单次执行超过图步数预算 |

响应约定：

| 情况 | HTTP 状态 | 当前提示 |
|---|---|---|
| 输入校验不通过 | 422 | FastAPI/Pydantic 默认字段错误信息 |
| 模型请求超时 | 504 | 模型响应超时 |
| 数据库连接或池故障 | 503 | 会话存储暂不可用 |
| 图执行步达到上限 | 503 | 本次处理步骤过多，请缩小查询范围后重试 |

这些处理覆盖 invoke() 中对应异常，不涵盖所有网络错误、SQL错误或启动故障。成功结果仍由 ChatResponse 返回 reply；未使用流式响应。

调用 config 除 configurable.thread_id 外，设置顶层 recursion_limit=12。每次 invoke 单独计算图执行预算，不限制整段会话轮数。并行工具调用数不与步数一一对应；精确调用次数限制需另行实现，可考虑 Agent 中间件。

已验证：纯空白消息及空会话ID返回422。未确认：超长输入、异常模拟、真实断连恢复、步数上限触发等测试结果。timeout=15 和 max_retries=2 不构成整次请求15秒内完成的保证。

## 8. Embedding 与知识向量库

### 向量模型

| 名称或配置 | 用途与当前行为 |
|---|---|
| create_embedding_model() | 返回 OpenAIEmbeddings；读取 app/.env，不在此展示密钥值 |
| EMBEDDING_MODEL | 指定向量模型；学习记录中接通的是百炼 qwen3.7-text-embedding，源码从环境变量读取，未在本文读取本地配置值 |
| EMBEDDING_API_KEY、EMBEDDING_BASE_URL | 分别指定向量服务凭据与兼容接口地址，与聊天模型配置独立 |
| dimensions=1024 | 向量维度，与知识表 vector_size 保持一致 |
| chunk_size=10 | 每批文本条数，不是知识片段长度 |
| check_embedding_ctx_length=False | 关闭客户端对应长度处理，仍需遵守服务端限制 |
| request_timeout=15、max_retries=2 | 当前网络请求配置，不构成整个入库过程的总耗时限制 |
| embed_query()、embed_documents() | 分别向量化问题和多段资料；实际调用会请求向量服务 |

独立入口为 `python -m app.rag.embedding`，会发送真实向量请求。学习记录确认曾返回1024维向量；创建封装对象本身不代表调用成功。兼容客户端需使用兼容接口路径，不直接套用原生 SDK 路径。

### 引擎与初始化

| 名称 | 用途与当前状态 |
|---|---|
| create_knowledge_engine() | 使用 sqlalchemy.URL.create() 组装数据库连接，再由 PGEngine.from_connection_string() 创建引擎 |
| PGHOST、PGPORT、PGDATABASE、PGUSER、PGPASSWORD | 数据库配置名称；与会话库共用配置来源，但知识引擎不是 main.py 中的 psycopg 连接池 |
| WindowsSelectorEventLoopPolicy | 当前 Python 3.12 Windows 环境的兼容配置，在创建引擎前设置 |
| init_vectorstore_table() | 脚本入口初始化 knowledge_chunks，vector_size=1024；不是每次请求执行的操作 |
| asyncio.run(engine.close()) | 初始化脚本 finally 中关闭引擎 |

学习记录确认项目数据库已启用 pgvector 0.6.0，知识表初始化成功；本文未重新连接数据库核查表结构、行数或权限。初始化表不等于写入知识，也不修改会话检查点用途。

### RAG模块与实际调用

| 名称 | 用途 |
|---|---|
| app/rag/engine.py：create_knowledge_engine() | 读取app/.env，组装SQLAlchemy URL，设置Windows兼容策略，创建PGEngine；与会话连接池分别管理 |
| app/rag/embedding.py：create_embedding_model() | 创建1024维向量封装 |
| app/rag/chunk_knowledge.py：split_markdown(file_path) | 读取Markdown，按标题分章节，普通章节递归切分，返回Document列表 |
| app/rag/knowledge.py：create_knowledge_store(engine) | 使用PGVectorStore.create_sync、embedding_service创建已有表的访问对象，不重新建表 |
| app/rag/import_knowledge.py：import_markdown(file_path, project_root) | 生成相对来源与UUID5，add_documents向量化并写入，finally关闭引擎 |
| app/tools/search_knowledge.py：create_search_knowledge_tool(store) | 工厂返回闭包工具，绑定已有store，供模型传入query |
| search_knowledge(query) | similarity_search(query,k=3)，返回results，每项含content、source、section；section取三级标题，缺失为空字符串 |

切分规则：普通章节chunk_size=700、chunk_overlap=100，len计字符；按段落、换行、中文标点等递归分割。含首尾管道符行的章节整体保留，这是Demo启发式，不是完整Markdown表格解析。片段加“主题”标题路径，metadata保留标题、source、chunk_index；入库时source替换为项目相对路径。整表章节可超过700字符，当前见1440字符片段。

稳定ID使用UUID5(来源路径+正文)。当前组件对相同ID执行更新，但重跑仍产生向量费用；正文变化产生新ID，旧记录不会自动删除。资料或向量模型变化需要另行清理或迁移。

命令及副作用：

- python -m app.rag.chunk_knowledge：读取并打印切分，纯本地。
- python -m app.rag.embedding：真实Embedding请求。
- python -m app.rag.import_knowledge：当前__main__只做固定问题的相似度检索，不调用import_markdown；需要SSH与问题向量化。不要将此入口描述为自动重新入库。
- python -m app.scripts.setup_knowledge：建表初始化，已有表不要覆盖或重复执行。

生命周期：

```text
启动 → 会话连接池 → PostgresSaver
     → PGEngine → PGVectorStore → search_knowledge工具
     → create_recommendation_agent(checkpointer, knowledge_tool)
请求 → 模型选择商品查询/知识检索 → 工具结果 → 完整回答
关闭 → await knowledge_engine.close() → pool.close()
```

两个数据库资源分别创建和释放；知识引擎内部异步不代表HTTP流式响应。当前接口仍一次性返回reply。

已验证证据：用户日志写入34片段；固定比较问题命中440C、China 440C和评级区别；工具轨迹与Basic材质回答确认知识工具参与。未据此认定全部知识正确、全部问题可召回，或正式商品推荐已通过。

## 9. Markdown 知识源与维护边界

| 路径 | 内容与用途 |
|---|---|
| knowledge/02宠物美容剪刀与工具/宠物美容剪刀.md | 品牌系列、钢材资料、剪型、尺寸、左右手及颜色；售前专业知识正文 |
| knowledge/03售后与维护/剪刀使用异常与维护.md | 使用养护、夹毛、推毛、开合异常、清洁润滑与收纳；售后知识正文 |
| knowledge/README.md | 目录、维护口径与后续导入建议，不作为知识正文导入 |
| docs/knowledge-maintenance.md | 保留推荐优先级、默认右手等行为规则；不入库，尚未接入提示词 |
| docs/knowledge-source-review.md | 外部来源摘要、访问局限及更正记录；不入库 |

维护口径：

- Basic通常对应9CR13练习与入门定位，Pro通常对应440C或China 440C日用主力、中高端定位，Master通常对应VG10高端定位；具体商品说明优先。
- 商品名称保留China 440C，材料属性按9CR18，使用性能参照440C属于品牌确认口径；不写成外部检测结论。
- 耐腐蚀、锋利度保持和抗崩口为品牌内部相对评级，不代表成品检测、初始锋利度或抗摔保证。
- 剪刀语境中的“寸”为英寸简称，标称尺寸不等于有效刃长；左右手重点区分刀片交叠结构，不能仅凭手柄判断。
- 推荐流程与默认条件保留在维护记录，尚未进入应用提示词；当前提示词已区分商品与知识工具，并明确不支持库存与销量排序；维护记录中的其他推荐规则仍需逐项确认是否接入。
- 外部资料的重要摘要已写入本地正文，链接用于追溯；文本检索不会因存在链接就自动访问网页。

后续导入按明确的正文文件范围执行，排除目录说明与维护文件；优先按标题切分，保留文档路径、标题层级、品牌、更新时间和来源。钢材资料卡及表头、评级性质应与正文保持关联。重新入库需替换旧片段，避免新旧版本同时命中；当前已实现单文件切分、入库与检索；尚未自动同步旧片段、品牌及更新时间等全部元数据，维护约定不等于全部落地。

图片当前仅用于人工辅助整理知识，尚未实现图片识别、图片检索或用户上传图片处理。

## 10. 文档维护约定

新增变量、函数或工具时记录用途、输入、输出、调用方和副作用；行为变更时同步更新。技术说明记录当前代码约定，开发日志记录变更原因、困难与验证结果。

## 11. 评测与客服规则（2026-10-29）

| 文件 | 用途与边界 |
|---|---|
| evals/run_langsimth.py | LangSmith评测入口，创建内存检查点Agent与知识工具；运行可能调用付费模型及向量服务，本次未执行 |
| evals/cases-active-v3.jsonl | 当前知识题集，50题含4道多轮题，排除未启用售后范围 |
| evals/cases-customer-v1.jsonl | 独立客服体验题集，24题；不与知识分数合并 |
| evals/test03.csv | 当前知识基线，复核得分178/200；单题一次，不代表稳定性 |
| evals/test04.csv、test05.csv | 客服实验结果；test04为195/240，test05完整评分待完成 |
| docs/evaluation-log.md | 评分口径、逐题依据、复核修订与风险记录 |
| docs/archive/ | 旧记录归档，不作为当前分数或提升幅度依据 |

当前提示词强调直接回答、必要时单个追问、已有证据可复用、查询失败不等于商品不存在；检索和商品内容仅作为资料。工具说明分别约束知识查询与实时商品查询，商品起售价不代表规格成交价，不能推断库存或销量排序。search_knowledge仍使用similarity_search(query,k=3)，说明文字改变不代表新增阈值、重排或售后资料入库。

评测解释：知识项包括工具选择、事实正确、边界准确和回答有效，每项0或1分；多轮审查全程。运行成功与工具选择评分均不等于实际工具执行成功。test05的问号轮次减少不能单独证明体验或可靠性提升，仍发现无依据材质及尺寸建议、换算错误和伪工具调用文本等失败。

版本边界：test03记录为v0.1.0-dirty，不能精确复现未提交源码；当前工作区不等于历史实验快照。后续需保存题集、知识范围、源码、提示词与运行配置，保持统一口径后比较。
