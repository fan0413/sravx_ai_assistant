# SRAVX 用户端商品推荐助手

状态：后端 Demo v0.1 核心能力已验证，版本标签尚未创建。更新：2026-10-26。

面向宠物美容师，结合商品接口和品牌知识库回答选购问题。采用完整响应：后台处理结束后一次性返回回答。当前通过 API 文档演示，尚无独立聊天页面，尚未接入商城用户端或生产部署。

## 已实现

- FastAPI POST /api/chat，输入 message、session_id，返回 reply。
- DeepSeek Agent：根据问题调用 search_products 或 search_knowledge。
- 商品关键词查询，当前演示结果包含“测试勿购”条目，不作为真实可购推荐。
- Markdown 标题切分、普通章节递归切分、含表章节整体保留、标题与来源附加。
- 百炼 Embedding，1024维；PGVectorStore + pgvector 存储及检索。
- PostgreSQL 检查点与连接池生命周期，基础跨重启会话恢复验证。
- 输入去空白和长度约束，部分异常状态映射及图执行步数预算。

## 目录

| 目录 | 作用 |
|---|---|
| app/agent、api、prompts、schemas | Agent组装、对话接口、规则与数据约束 |
| app/tools | 商品查询与知识检索工具 |
| app/rag | Embedding、切分、向量库引擎、入库函数及检索演示入口 |
| app/scripts | 数据库表初始化脚本，不随聊天请求运行 |
| knowledge | 原始 Markdown 知识正文 |
| docs | 技术说明、开发日志与知识维护记录 |

## 环境与启动

开发环境：Python 3.12；关键组件已核实为 langchain-postgres 0.0.19、langchain-openai 1.1.11、langgraph-checkpoint-postgres 3.0.5、psycopg 3.3.3、psycopg-pool 3.3.0。

注意：当前 requirements 清单尚未包含 langchain-postgres，复现时需额外安装；正式封版前将其加入依赖清单。

```powershell
python -m pip install -r requirements.txt
python -m pip install "langchain-postgres==0.0.19"
```

配置放在 app/.env，不提交 Git。配置名称包括 DEEPSEEK_API_KEY、PGHOST、PGPORT、PGDATABASE、PGUSER、PGPASSWORD、EMBEDDING_MODEL、EMBEDDING_API_KEY、EMBEDDING_BASE_URL。聊天模型当前在代码中指定；向量服务使用 OpenAI 兼容 base_url，不是 DashScope 原生 API 路径。不要复制或输出真实凭据。

开发阶段先保持独立 SSH 隧道运行：本地127.0.0.1:15432转发至数据库服务器127.0.0.1:5432。私钥使用本机受限文件，位于 Git 排除范围；DataGrip 隧道不自动供 Python 使用。

已有检查点和知识表无需重复建表。首次空库准备方法见技术说明；当前项目库已启用 pgvector 0.6.0。

在项目根目录、已激活环境的终端运行：

```powershell
python -m uvicorn app.main:app --reload
```

打开 http://127.0.0.1:8000/docs，选择 POST /api/chat。根路径未配置，访问 / 返回404属于预期。

## 演示顺序

使用新的 session_id，例如 demo-v01-01，依次输入：

1. “SRAVX Basic一般用什么钢材？”——检查调用轨迹出现 search_knowledge，回答保留“通常对应”与非成品检测的边界。
2. “China 440C和440C有什么区别？”——检查根据知识片段解释材料属性与品牌使用性能口径。
3. “帮我查直剪。”——检查 search_products，明确测试商品不可作为真实购买建议。
4. 在测试会话提供无敏感信息的选购编号，重启服务后用同一ID追问，验证历史恢复。

这些请求会产生模型和向量服务调用费用。返回200不单独代表答案准确；工具执行以完整轨迹中的调用和 ToolMessage 为依据。

## 知识处理入口

- python -m app.rag.chunk_knowledge：仅预览切分，不调用模型或数据库。
- python -m app.rag.embedding：真实向量请求，验证1024维结果。
- python -m app.rag.import_knowledge：当前直接运行只做相似度检索演示；import_markdown() 函数负责入库，不能把运行命令误认为重新导入。
- app/scripts/setup_knowledge.py：初始化知识表；已有表不要重跑或覆盖。
- app/scripts/seup_checkpoints.py：初始化会话检查点；保留当前文件名。

已由用户运行日志确认写入34个片段；本次收尾未重新查询数据库行数。当前稳定UUID可更新同来源同内容的记录，但重导仍会产生Embedding费用，内容变化后的旧片段不会自动清除。入库与检索入口后续应进一步分离。

## Demo边界

- 单文件知识已验证，不代表售后文档或整个 knowledge 目录均已入库。
- 没有登录与会话归属校验，不对公网开放；跨会话授权、并发和完整异常恢复尚未验收。
- 商品仅关键词检索前5条，不支持完整目录、销量排序或实时SKU库存判断。
- 未实现自动资料更新、旧向量清理、检索阈值或重排；向量模型、维度改变需另行迁移。
- 不执行改价、发布、订单、退款、优惠承诺等操作。

## 文档

- [立项与实施步骤](docs/project-plan.md)
- [学习开发日志](docs/development-log.md)
- [技术说明](docs/technical-reference.md)

密钥、私钥、生产配置、客户资料、数据库内容及敏感调用日志不得提交。
