# 立项与实施步骤

日期：2026-10-19

## 目标与事实

目标：学习 Agent 开发，以用户端商品推荐为首个功能，最终接入 SRAVX 商城。
商城主目录为 E:/sravxapp，当前助手学习目录为 E:/sravx_ai_assistant。
用户已澄清尚未开始模型初始化；模型服务商、模型、预算均待确定。

## Harness 与框架的决定

Harness 在这里指包住模型的运行程序：管理消息、公布工具、校验参数、执行工具、回传结果并限制循环。
它不是必须购买或安装的特定产品。建议第一版用 Node.js 和服务商 SDK/HTTP 接口实现小型 harness；框架后续按复杂度决定。
单个只读工具暂不需要多 Agent、向量数据库、MCP 服务或复杂编排。
这属于建议，技术依赖尚未选定。

参考：https://www.anthropic.com/engineering/building-effective-agents

## 实施步骤与验收

1. 确定服务商：按可用性、中文理解、原生工具调用、数据处理条款和预算选择；查官方文档后确定 SDK 与配置。
   验收：确认可用模型和费用边界，不在未授权时购买或充值。
2. 模型初始化：本地环境变量存放服务地址、模型名和密钥；仅提交不含值的配置示例。
   验收：一次最小文本请求成功；错误不会输出密钥。
3. 查询工具：定义 JSON 参数结构、允许的枚举、返回数量和精简商品字段；先用固定模拟数据跑通。
   验收：正常查询、空结果、非法参数、超时都返回明确结果。
4. 工具调用循环：接收模型工具请求，程序校验并执行，按服务商协议回传调用 ID 和结果，再让模型回答。
   验收：不执行未知工具，限制轮数、时长与结果大小；失败不伪造商品。
5. 连接真实查询：只读商品目录，抽取字段并核对规格价格；不使用管理端写接口。
   验收：推荐商品 ID 能查回；价格对应具体规格；不把上架等同有货。
6. 用户页面集成：复用商城后端权限与接口边界，密钥仅服务端保存。
   验收：本地端到端通过后再另行安排上线。

## 已核对接口及限制

- GET /api/v1/catalog/products：keyword、categoryId、series、toolGroup、page、pageSize。
- GET /api/v1/catalog/products/:id：商品与规格详情。
- toolSubtype、size 仅 STRUCTURED_CHECKOUT_ENABLED 开启时参与过滤；线上开关尚未核实。
- series：basic/pro/master/accessories。
- toolGroup：straight/curved/thinning/fishbone/texturizing/accessories。
- 列表默认20条，最多100条；data 为数组，没有 total；没有价格区间或相关度排序参数。
- 只返回上架且分类可见的商品，但不排除缺货。
- price 为元单位的最低规格展示价；base_price 是保留的原商品价格，不能假定为成交价。
- 结构化 SKU 的 price_fen 单位为分；详情字段随功能开关不同。
- COS 签名图片地址有效期15分钟。
- 实际字段完整度和生产可用性尚未核实。

## GitHub 准备

仓库名称、归属账号与公开性待用户确定。建议公开前审查文档、测试数据及商品资料的披露范围。
本机 Git 和 GitHub CLI 可用；本次检查 GitHub CLI 尚未登录。
确定仓库设置后，由用户完成交互登录，再创建空仓库并提交审查后的源码与文档。
GitHub 仓库用于版本管理；暂不需要另建 GitHub Projects 看板。
