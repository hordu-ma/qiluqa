# 代码评审报告（chatomni-local-qa-qilumed-dev）

## 范围与方法
- 读取的主要文件：`api.py`、`config/base_config.py`、`config/base_config_chatglm4.py`、`config/prod/prod_config_dashscope.py`、`models/llms/llms_adapter.py`、`models/chains/chain_model.py`、`models/vectordatabase/v_client.py`、`service/local_repo_service.py`、`service/chat_private_service.py`、`service/chat_public_service.py` 等。
- 关注点：可复用性、配置与安全、适配层可扩展性、健壮性与潜在缺陷。

## 主要发现与风险

### P0（高优先级）
- **大量硬编码密钥**：`config/base_config.py:119,134-136`、`config/base_config_chatglm4.py:1-4`、`config/prod/prod_config_dashscope.py:1-4` 直接包含 API Key / AES 密钥等敏感信息，且随代码分发，存在泄露与环境隔离失效风险。应迁移到环境变量或密钥管理，并立即轮换。
- **向量库/模型选择的默认逻辑缺陷**：`config/base_config.py:22-23` 中 `CURRENT_LLM = "DashScope" or DEFAULT_LLM` 使配置始终固定为 DashScope，无法通过环境变量切换；`models/vectordatabase/v_client.py:15-18` 在非 Postgres 分支仅 `pass`，调用方会得到 `None` 并在运行期抛异常，阻断复用。

### P1（中优先级）
- **跨平台与目录安全性问题**：`config/base_config.py:58` 默认 `CONTENT_PATH` 为 Windows 绝对路径，Linux/macOS 下将直接失效；`api.py:168-200` 上传接口把文件直接写入该路径，未确保目录存在或做路径拼接校验，存在运行失败与潜在路径穿越风险。
- **配置与依赖耦合过深，`import *` 泛滥**：如 `api.py:24`、`models/llms/llms_adapter.py:5`、`service/local_repo_service.py:13`。模块初始化即加载全量配置与依赖，难以做按场景注入/Mock，后续新增环境或重构配置会牵一发动全身，降低复用性和可测试性。
- **适配器/分发模式难以扩展**：LLM/Embedding/Vector 均使用 if/elif 固定分支（`models/llms/llms_adapter.py:56-84`、`models/embeddings/es_model_adapter.py:24-37`、`models/vectordatabase/v_client.py:15-18`），新增实现需要改动核心文件且缺少默认失败提示，易引入回归。
- **可变默认参数导致状态污染风险**：`models/llms/llms_adapter.py:42-46`、`models/chains/chain_model.py:134-141` 使用 `history=[]`、`images=[]` 作为默认参数，跨请求复用时可能残留上次调用的数据。
- **检索结果过滤逻辑异常**：`service/local_repo_service.py:164-180` 仅保留得分等于 0 或小于阈值/大于 1 的文档，正常得分的结果会被全部丢弃，导致召回质量不可控。
- **API 层与业务/IO 混杂**：`api.py:168-200` 同时处理上传、文件写入、向量化调用，且混用 `print` 与 logger，缺少失败回收逻辑；定时任务在 `startup` 直接启动（`api.py:103-121`），多进程部署可能重复调度。
- **流式与非流式问答重复实现**：`service/chat_private_service.py` 与 `service/chat_public_service.py` 中的 `ask`/`ask_stream` 均重复了机器人校验、历史查询、插件处理与召回逻辑，后续修复/增强容易遗漏某一分支，降低复用性。

### P2（低优先级）
- **Prompt 分散且缺少统一管理**：`models/chains/chain_model.py:33-47` 与 `content/prompt_template*.py` 等各处均有内联 prompt，缺少集中目录与版本管理，不利于跨项目共享。
- **异常处理过于宽泛**：`models/vectordatabase/v_client.py:14-21` 等处直接捕获 `Exception` 且未补充上下文或重抛细节，定位问题成本高。
- **缺少自动化验证**：仓库未见测试/CI 配置，配置与适配器层的缺陷（如前述路径、默认参数）难以及早暴露。

## 可复用性改进建议
- **配置收敛与环境隔离**：构建 `settings`/`pydantic` 配置对象，移除 `import *`，仅暴露必要字段；通过 `.env`/部署平台 Secret 管理密钥，并把路径、模型、向量库等作为可注入参数。
- **注册表/插件化的适配层**：为 LLM、Embedding、Vector 建立简单的注册表（`dict` 或 entry points），新增实现仅需注册，不修改核心逻辑；未注册模型时抛出显式错误，便于复用与扩展。
- **抽取问答公共流程**：把机器人校验、历史拉取、插件、召回、metadata 拼装封装为共享方法，`ask` 负责同步生成，`ask_stream` 仅处理流式事件，减少重复。
- **健壮性与跨平台**：`CONTENT_PATH` 改为 `Path` 拼接并在启动时确保目录存在；修复检索过滤逻辑；替换可变默认参数为 `None` + 运行期初始化；统一使用 logger。
- **调度与运行模型可配置化**：为 APScheduler 增加锁或单实例标识，避免多 worker 重复执行；修正 `CURRENT_LLM` 与向量库选择逻辑以尊重环境与配置。
- **Prompt/模板治理**：集中存放 prompt，并按场景/版本命名，供各自 API/业务引用，便于后续 A/B 与跨项目共享。

## 后续建议
- 在修复上述高优先级问题后，补充最小化的集成测试（配置加载、问答链路、检索过滤、上传）与 CI，以防止再次引入配置与适配器层回归。

