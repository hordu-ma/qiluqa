# Config 目录配置架构文档

> 生成时间：2025-12-28  
> 文档说明：医疗问答系统配置管理完整架构解析

---

## 📋 概述

这是一个 **多环境配置管理系统**，采用分层配置策略，支持测试环境和生产环境的灵活切换，管理 LLM 模型、数据库、向量库、业务参数等所有系统配置。

---

## 📁 目录结构

```
config/
├── 基础配置层（Base Config）
│   ├── base_config.py               # 核心配置入口（环境切换）
│   ├── base_config_dashscope.py     # 阿里百炼模型配置
│   ├── base_config_deepseek.py      # DeepSeek 模型配置
│   ├── base_config_openai.py        # OpenAI 模型配置
│   ├── base_config_chatglm4.py      # 智谱 ChatGLM4 配置
│   ├── base_config_vector.py        # 向量库基础配置
│   ├── base_config_model_type.py    # 模型类型常量
│   └── loguru_config.py             # 日志框架配置
│
├── test/                            # 测试环境配置
│   ├── test_base_config.py          # 测试环境基础配置
│   ├── test_config_dashscope.py     # 测试环境百炼配置
│   ├── test_config_deepseek.py      # 测试环境 DeepSeek 配置
│   ├── test_config_mysql.py         # 测试环境 MySQL 配置
│   ├── test_config_postgres.py      # 测试环境 PostgreSQL 配置
│   └── test_config_redis.py         # 测试环境 Redis 配置
│
└── prod/                            # 生产环境配置
    ├── prod_base_config.py          # 生产环境基础配置
    ├── prod_config_dashscope.py     # 生产环境百炼配置
    ├── prod_config_deepseek.py      # 生产环境 DeepSeek 配置
    ├── prod_config_mysql.py         # 生产环境 MySQL 配置
    ├── prod_config_postgres.py      # 生产环境 PostgreSQL 配置
    └── prod_config_redis.py         # 生产环境 Redis 配置
```

---

## 🎯 核心配置文件详解

### 1. `base_config.py` - 配置中枢

**定位**：系统配置的总入口，负责环境切换和配置聚合。

**核心机制**：

#### 1.1 环境切换机制

```python
# 环境标识符
ENV_TEST = "test"
APPLICATION_ENV = os.environ.get("APPLICATION_ENV") or ENV_TEST
APPLICATION_ENV_IS_TEST = (APPLICATION_ENV == ENV_TEST)
```

**环境判断逻辑**：
- 通过环境变量 `APPLICATION_ENV` 控制
- 默认为测试环境（`test`）
- 所有配置项根据 `APPLICATION_ENV_IS_TEST` 自动切换

**示例**：
```python
# 数据库配置自动切换
MYSQL_HOST = TEST_MYSQL_HOST if APPLICATION_ENV_IS_TEST else PROD_MYSQL_HOST
MYSQL_PORT = TEST_MYSQL_PORT if APPLICATION_ENV_IS_TEST else PROD_MYSQL_PORT
```

---

#### 1.2 配置分类

| 配置类别 | 配置项 | 说明 |
|---------|-------|------|
| **LLM 模型** | `CURRENT_LLM` | 当前使用的 LLM 厂商（DashScope/DeepSeek/OpenAI） |
| | `OPENAI_API_KEY` | OpenAI API 密钥 |
| | `OPENAI_MODEL_NAME` | OpenAI 模型名称（默认 gpt-4-turbo-preview） |
| **向量库** | `VECTOR_DATABASE_TYPE` | 向量库类型（Postgres + pgvector） |
| | `VECTOR_EMBEDDINGS_MODEL` | 嵌入模型（DashScope/OpenAI） |
| | `PGVECTOR_HOST` | PostgreSQL 地址 |
| | `PGVECTOR_DIMENSIONS` | 向量维度 |
| **业务数据库** | `MYSQL_HOST` | MySQL 地址 |
| | `MYSQL_DATABASE` | 数据库名称 |
| | `MYSQL_USER` / `MYSQL_PASSWD` | 认证信息 |
| **缓存** | `REDIS_HOST` | Redis 地址 |
| | `REDIS_DATABASE` | Redis DB 编号 |
| **文件存储** | `CONTENT_PATH` | 上传文件临时目录 |
| | `SPIDER_FILE_PATH` | 爬虫文件保存路径 |
| **分片策略** | `SPLIT_CHUNK_SIZE` | 默认分片大小（800） |
| | `SPLIT_CHUNK_OVERLAP` | 分片重叠值（100） |
| | `VECTOR_SEARCH_TOP_K` | 召回分片数量（2） |
| | `VECTOR_SEARCH_SCORE` | 相似度阈值（0.6） |
| **记忆管理** | `MEMORY_LIMIT_SIZE` | 历史记忆轮数（2） |
| **定时任务** | `SCHEDULES_ENABLED` | 是否启用定时任务 |
| | `SCHEDULES_RATE_SECOND` | 文件向量化任务间隔（10秒） |
| | `SCHEDULES_PROHIBITED_SECONDS` | 违禁词更新间隔（1天） |
| | `SCHEDULES_DISCLAIMER_SECONDS` | 免责声明更新间隔（1天） |
| | `SCHEDULES_SPIDER_SECONDS` | 网页爬虫更新间隔（1小时） |
| **业务配置** | `DEFAULT_CHAT_BOT_ROLE` | 默认机器人角色 |
| | `TAVILY_API_KEY` | Tavily 搜索 API 密钥 |
| | `HTTP_HOST` | 服务地址 |
| **专用模型** | `INTENTION_RECOGNITION_MODEL` | 意图识别模型 |
| | `QUES_OPTIMIZER_MODEL` | 问题优化模型 |
| | `FILES_SUMMARY_MODEL` | 文件摘要模型 |
| | `THINKING_MODEL` | 深度思考模型 |
| **安全** | `AES_IV` / `AES_KEY` | AES 加密密钥 |

---

#### 1.3 分片策略常量

```python
CHUNK_STRATEGY_SMART = '111'                      # 智能分片
CHUNK_STRATEGY_TEXT_LENGTH = '211'               # 按长度分片
CHUNK_STRATEGY_TEXT_SENTENCE = '212'             # 按句子分片
CHUNK_STRATEGY_TEXT_SENTENCE_BY_WINDOW = '212_1' # 滑动窗口句子分片
CHUNK_STRATEGY_TEXT_SEMANTICS = '213'            # 按语义分片
CHUNK_STRATEGY_TEXT_QA = '214'                   # QA 分片
CHUNK_STRATEGY_TEXT_EXCEL = '215'                # Excel 分片
CHUNK_STRATEGY_TEXT_PICTURE = '216'              # 图片分片
CHUNK_STRATEGY_TEXT_NO_CHUNK = '217'             # 不分片
```

**应用场景**：
- 根据文件类型和业务需求选择合适的分片策略
- 在 `AiChunkStrategyDomain.switch_case_by_chunk_strategy()` 中调用

---

#### 1.4 免责声明模板

```python
# 有溯源信息
DEFAULT_HAVE_TRACE = '以上是参考了【{trace_content}】结合人工智能技术所提供的内容，可能存在一定的局限性。建议您在使用时谨慎判断，咨询相关领域的专业人士或参考更多来源的信息进行验证。'

# 无溯源信息
DEFAULT_NOT_TRACE = '以上是由人工智能技术所提供的内容，仅作为参考，并不能替代专业的意见或建议。在做出任何决策之前，建议您综合考虑多方信息，并咨询相关领域的专业人士。'
```

---

### 2. LLM 厂商配置

#### 2.1 `base_config_dashscope.py` - 阿里百炼

**核心配置**：

```python
# 模型配置
BASHSCOPE_MODEL_NAME = "qwen3-30b-a3b"          # 默认模型
BASHSCOPE_MODEL_TYPE = MODEL_TYPE_TEXT          # 模型类型（文本/视觉/音频）
BASHSCOPE_MAX_TOKENS = 8192                     # 最大输出 token 数

# 推理参数
BASHSCOPE_TEMPERATURE = 0.85                    # 温度（控制随机性）
BASHSCOPE_TOP_P = 0.9                           # 核采样参数
BASHSCOPE_TOP_K = 999                           # Top-K 采样

# 多端点配置（环境自动切换）
BASHSCOPE_BASE_URL = TEST/PROD_BASHSCOPE_BASE_URL         # 文本模型端点
BASHSCOPE_THINKING_URL = TEST/PROD_BASHSCOPE_THINKING_URL # 思维链模型端点
BASHSCOPE_VL_URL = TEST/PROD_BASHSCOPE_VL_URL             # 视觉模型端点

# API 认证
BASHSCOPE_API_KEY = TEST/PROD_BASHSCOPE_API_KEY

# 安全控制
BASHSCOPE_SECURE_ANSWER = "用户输入存在安全风险，建议关闭当前会话，清理历史会话信息。"
```

**特点**：
- 支持多模态（文本 + 视觉）
- 独立的思维链模型端点
- 自动切换测试/生产环境 API Key

---

#### 2.2 `base_config_deepseek.py` - DeepSeek

**核心配置**：

```python
# 多 API Key 池（负载均衡）
DEEPSEEK_API_KEY_POOL = TEST/PROD_DEEPSEEK_API_KEY_POOL

# 端点配置
DEEPSEEK_URL = TEST/PROD_DEEPSEEK_URL

# 模型参数
DEEPSEEK_MODEL_NAME = "deepseek-chat"
DEEPSEEK_MAX_TOKENS = 8192
DEEPSEEK_TEMPERATURE = 0.8
```

**特点**：
- 支持 API Key 池（多 Key 轮询）
- 简洁配置

---

#### 2.3 `base_config_openai.py` - OpenAI

**核心配置**：

```python
BASE_OPENAI_API_KEY = None                          # 需环境变量配置
BASE_OPENAI_MODEL_NAME = "gpt-4-turbo-preview"     # 默认模型
BASE_OPENAI_TEMPERATURE = 0.7
BASE_OPENAI_OUTPUT_TOKEN_LENGTH = 2048
```

---

#### 2.4 `base_config_chatglm4.py` - 智谱 AI

**核心配置**：

```python
CHATGLM4_MODEL_NAME = 'glm-4'
CHATGLM4_URL = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
CHATGLM4_API_KEY = '02fc0a8ebfbb73fbdc09e7d587ae7acd.IBEvo9d9kRjMmy9A'
CHATGLM4_TEMPERATURE = 0.5
CHATGLM4_TOP_P = 0.5
CHATGLM4_MAX_TOKENS = 5000
```

---

### 3. 向量库配置

#### `base_config_vector.py`

```python
# 向量库类型
BASE_VECTOR_DATABASE_TYPE = "Postgres"  # 使用 PostgreSQL + pgvector

# 嵌入模型配置
BASE_VECTOR_EMBEDDINGS_MODEL = "DashScope"          # 向量化服务
BASE_VECTOR_EMBEDDINGS_MODEL_TYPE = "text-embedding-v1"  # 嵌入模型类型
```

**向量库连接配置**（在 `base_config.py` 中）：
```python
PGVECTOR_DRIVER = "postgresql+psycopg2"
PGVECTOR_HOST = "localhost"
PGVECTOR_PORT = 5432
PGVECTOR_DATABASE = "vector_db"
PGVECTOR_USER = "postgres"
PGVECTOR_PASSWORD = "password"
PGVECTOR_DIMENSIONS = 1536  # 向量维度（与嵌入模型匹配）
```

---

### 4. 模型类型常量

#### `base_config_model_type.py`

```python
MODEL_TYPE_TEXT = "text"    # 纯文本模型
MODEL_TYPE_VL = "vl"        # 视觉语言模型（Vision-Language）
MODEL_TYPE_AUDIO = "audio"  # 音频模型（预留）
```

**应用场景**：
- 在 `ChainModel` 中根据模型类型选择不同端点
- Vision 模型需要传递图片 URL

---

### 5. 日志配置

#### `loguru_config.py`

```python
def init_log_config():
    # INFO 级别日志
    logger.add(
        sink='./log/info.log',
        rotation='00:00',        # 每天 0 点滚动
        retention='30 days',     # 保留 30 天
        level="INFO",
        encoding='utf8',
        enqueue=True,           # 异步写入
        serialize=True,         # 序列化为 JSON
    )

    # ERROR 级别日志（单独文件）
    logger.add(
        sink='./log/error.log',
        rotation='00:00',
        retention='30 days',
        level="ERROR",
        encoding='utf8',
        enqueue=True,
        serialize=True,
        filter=lambda record: record["level"].name == "ERROR",
    )
```

**特点**：
- 分级存储（INFO / ERROR 分离）
- 自动日志滚动（每日 0 点）
- 异步写入（提高性能）
- JSON 格式（便于日志分析）

---

## 🔄 环境配置详解

### 测试环境（`test/`）

#### `test_base_config.py`

```python
TEST_HTTP_HOST = "http://47.236.254.2"

# 专用模型配置（测试环境使用轻量级模型）
TEST_INTENTION_RECOGNITION_MODEL = "DashScope"
TEST_INTENTION_RECOGNITION_MODEL_NAME = "qwen3-30b-a3b"     # 30B 模型

TEST_QUES_OPTIMIZER_MODEL = "DashScope"
TEST_QUES_OPTIMIZER_MODEL_NAME = "qwen3-30b-a3b"

TEST_FILES_SUMMARY_MODEL = "DashScope"
TEST_FILES_SUMMARY_MODEL_NAME = "qwen3-30b-a3b"

TEST_THINKING_MODEL = "DashScope"
TEST_THINKING_MODEL_NAME = "qwen3-32b"                      # 思维链模型
```

---

### 生产环境（`prod/`）

#### `prod_base_config.py`

```python
PROD_HTTP_HOST = "http://172.18.6.117"

# 专用模型配置（生产环境使用高性能模型）
PROD_INTENTION_RECOGNITION_MODEL = "DashScope"
PROD_INTENTION_RECOGNITION_MODEL_NAME = "qwen3-235b-instruct"  # 235B 大模型

PROD_QUES_OPTIMIZER_MODEL = "DashScope"
PROD_QUES_OPTIMIZER_MODEL_NAME = "qwen3-235b-instruct"

PROD_FILES_SUMMARY_MODEL = "DashScope"
PROD_FILES_SUMMARY_MODEL_NAME = "qwen3-235b-instruct"

PROD_THINKING_MODEL = "DashScope"
PROD_THINKING_MODEL_NAME = "qwen3-235b-think"                  # 专用思维链模型
```

**环境差异总结**：

| 配置项 | 测试环境 | 生产环境 |
|--------|---------|---------|
| **服务地址** | 公网 IP | 内网 IP |
| **意图识别模型** | qwen3-30b-a3b | qwen3-235b-instruct |
| **问题优化模型** | qwen3-30b-a3b | qwen3-235b-instruct |
| **文件摘要模型** | qwen3-30b-a3b | qwen3-235b-instruct |
| **思维链模型** | qwen3-32b | qwen3-235b-think |
| **数据库连接** | 测试库 | 生产库 |
| **向量库** | 测试向量库 | 生产向量库 |

---

## 🎨 配置设计模式

### 1. 分层配置（Layered Configuration）

```
┌─────────────────────────────────────────────┐
│ base_config.py（配置聚合层）                 │
│ - 环境切换逻辑                               │
│ - 配置项统一出口                             │
└─────────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────────┐
│ 基础配置层（Base Config）                    │
│ - base_config_dashscope.py                  │
│ - base_config_deepseek.py                   │
│ - base_config_vector.py                     │
└─────────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────────┐
│ 环境配置层（Environment Config）             │
│ - test/* （测试环境）                        │
│ - prod/* （生产环境）                        │
└─────────────────────────────────────────────┘
```

---

### 2. 环境切换策略（Environment Strategy）

**核心思想**：通过环境变量 `APPLICATION_ENV` 一键切换所有配置。

**实现方式**：
```python
# 1. 定义环境标识
APPLICATION_ENV_IS_TEST = (APPLICATION_ENV == ENV_TEST)

# 2. 所有配置项使用三元表达式
MYSQL_HOST = TEST_MYSQL_HOST if APPLICATION_ENV_IS_TEST else PROD_MYSQL_HOST

# 3. 导入时自动选择
from config.test.test_config_mysql import TEST_MYSQL_HOST
from config.prod.prod_config_mysql import PROD_MYSQL_HOST
```

**优势**：
- 无需修改代码即可切换环境
- 避免配置文件误用
- 配置变更集中管理

---

### 3. 模块化配置（Modular Configuration）

**按功能模块拆分配置文件**：

```
LLM 配置    → base_config_dashscope.py
            → base_config_deepseek.py
            → base_config_openai.py

数据库配置  → test/prod_config_mysql.py
            → test/prod_config_postgres.py
            → test/prod_config_redis.py

向量库配置  → base_config_vector.py
```

**优势**：
- 职责分离，易于维护
- 便于扩展新的 LLM 厂商
- 减少配置冲突

---

### 4. 默认值 + 环境变量覆盖

```python
# 1. 设置默认值
OPENAI_API_KEY = BASE_OPENAI_API_KEY

# 2. 允许环境变量覆盖
OPENAI_API_KEY = BASE_OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
```

**优势**：
- 开发环境使用默认值（快速启动）
- 生产环境使用环境变量（安全）
- 灵活性强

---

## 💡 核心配置应用场景

### 场景 1：切换 LLM 厂商

```python
# 方式 1：修改 base_config.py
CURRENT_LLM = "DashScope"  # 或 "DeepSeek" / "OpenAI"

# 方式 2：环境变量
export DEFAULT_LLM="DeepSeek"
```

**影响范围**：
- `LLMsAdapter` 自动选择对应厂商
- 所有问答服务自动切换模型

---

### 场景 2：调整分片策略

```python
# 修改默认分片大小
SPLIT_CHUNK_SIZE = 1024  # 从 800 调整到 1024

# 修改重叠值
SPLIT_CHUNK_OVERLAP = 200  # 从 100 调整到 200

# 调整召回数量
VECTOR_SEARCH_TOP_K = 5  # 从 2 调整到 5
```

---

### 场景 3：环境切换

```bash
# 切换到测试环境
export APPLICATION_ENV=test

# 切换到生产环境
export APPLICATION_ENV=prod
```

**自动生效的配置**：
- 数据库连接（MySQL/PostgreSQL/Redis）
- LLM 模型（测试用轻量级，生产用高性能）
- 服务地址（HTTP_HOST）

---

### 场景 4：启用/禁用定时任务

```python
# 全局开关
SCHEDULES_ENABLED = False  # 禁用所有定时任务

# 单独控制
SCHEDULES_PROHIBITED = False      # 禁用违禁词更新
SCHEDULES_DISCLAIMER = False      # 禁用免责声明更新
SCHEDULES_SPIDER = False          # 禁用网页爬虫
```

---

### 场景 5：专用模型配置

**问题**：不同业务场景需要不同模型能力。

**解决方案**：配置专用模型。

```python
# 意图识别（需要快速响应）
INTENTION_RECOGNITION_MODEL = "DashScope"
INTENTION_RECOGNITION_MODEL_NAME = "qwen3-30b-a3b"  # 轻量级模型

# 问题优化（需要高质量改写）
QUES_OPTIMIZER_MODEL = "DashScope"
QUES_OPTIMIZER_MODEL_NAME = "qwen3-235b-instruct"  # 大模型

# 深度思考（需要推理能力）
THINKING_MODEL = "DashScope"
THINKING_MODEL_NAME = "qwen3-235b-think"  # 专用思维链模型
```

---

## 📊 配置依赖关系图

```
┌────────────────────────────────────────────────────────┐
│ API 层（FastAPI）                                       │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Service 层                                              │
│ - 读取配置：HTTP_HOST, TAVILY_API_KEY                   │
│ - 调用模型：INTENTION_RECOGNITION_MODEL                 │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Models 层（LLMsAdapter）                                │
│ - 读取配置：CURRENT_LLM                                 │
│ - 根据厂商选择：                                        │
│   • DashScope → BASHSCOPE_API_KEY                      │
│   • DeepSeek → DEEPSEEK_API_KEY_POOL                   │
│   • OpenAI → OPENAI_API_KEY                            │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ 基础设施层                                              │
│ - 数据库：MYSQL_HOST, PGVECTOR_HOST                    │
│ - 缓存：REDIS_HOST                                      │
│ - 日志：loguru_config                                   │
└────────────────────────────────────────────────────────┘
```

---

## 🚀 配置最佳实践

### 1. 敏感信息管理

**❌ 不推荐**：
```python
OPENAI_API_KEY = "sk-xxxxxxxxxxxxxxxx"  # 硬编码
```

**✅ 推荐**：
```python
# 方式 1：环境变量
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# 方式 2：.env 文件（使用 python-dotenv）
from dotenv import load_dotenv
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```

---

### 2. 环境隔离

**原则**：测试环境和生产环境完全隔离。

```
测试环境：
- 数据库：test_db
- 向量库：test_vector_db
- 模型：轻量级（qwen3-30b）
- 服务地址：公网 IP（便于调试）

生产环境：
- 数据库：prod_db
- 向量库：prod_vector_db
- 模型：高性能（qwen3-235b）
- 服务地址：内网 IP（安全）
```

---

### 3. 配置验证

**启动时检查必要配置**：

```python
def validate_config():
    """配置验证"""
    required_configs = [
        ("CURRENT_LLM", CURRENT_LLM),
        ("MYSQL_HOST", MYSQL_HOST),
        ("PGVECTOR_HOST", PGVECTOR_HOST),
    ]
    
    for name, value in required_configs:
        if not value:
            raise ValueError(f"配置项 {name} 未设置！")
```

---

### 4. 配置热更新（可选）

**适用场景**：需要动态调整模型参数（如 temperature）。

**实现方式**：
```python
# 1. 从配置中心（如 Nacos）拉取配置
# 2. 动态更新全局变量
# 3. 重新初始化 LLM 实例
```

---

### 5. 配置文档化

**为每个配置项添加注释**：

```python
# 向量检索相似度阈值
# 值越高，召回的分片越精确但数量越少
# 推荐范围：0.5 - 0.8
VECTOR_SEARCH_SCORE = 0.6
```

---

## ⚠️ 注意事项

### 1. API Key 安全

- **禁止**将 API Key 提交到 Git 仓库
- 使用 `.gitignore` 忽略包含密钥的文件
- 生产环境使用环境变量或密钥管理服务（如 AWS Secrets Manager）

---

### 2. 配置同步

- 测试环境和生产环境的配置结构应保持一致
- 新增配置项时同步更新 `test/` 和 `prod/`
- 使用版本控制跟踪配置变更

---

### 3. 默认值设置

- 为所有配置项设置合理的默认值
- 默认值应适用于开发环境
- 生产环境必须显式配置关键参数

---

### 4. 环境变量命名

- 使用统一的命名规范（如全大写、下划线分隔）
- 避免与系统环境变量冲突
- 添加前缀以区分项目（如 `CHATOMNI_`）

---

### 5. 配置变更影响评估

**重要配置变更前需评估影响**：

| 配置项 | 影响范围 | 风险等级 |
|--------|---------|---------|
| `CURRENT_LLM` | 所有 LLM 调用 | 🔴 高 |
| `VECTOR_SEARCH_TOP_K` | RAG 召回质量 | 🟡 中 |
| `SPLIT_CHUNK_SIZE` | 已入库数据需重新处理 | 🟡 中 |
| `MEMORY_LIMIT_SIZE` | 对话上下文长度 | 🟢 低 |
| `SCHEDULES_RATE_SECOND` | 定时任务频率 | 🟢 低 |

---

## 🔍 常见问题

### Q1: 如何新增 LLM 厂商配置？

**步骤**：
1. 在 `config/` 下创建 `base_config_xxx.py`
2. 定义厂商特定配置（API Key、端点、模型名等）
3. 在 `test/` 和 `prod/` 下创建对应环境配置
4. 在 `base_config.py` 中导入并使用
5. 在 `LLMsAdapter` 中添加适配逻辑

---

### Q2: 为什么分片大小是 800？

**原因**：
- 平衡召回精度和上下文完整性
- 800 字符约 400 中文字，适合大部分场景
- 根据实际业务调整（长文档建议 1024-2048）

---

### Q3: 如何调试配置问题？

**方法**：
```python
# 启动时打印当前环境
logger.info(f"当前环境：{APPLICATION_ENV}")
logger.info(f"LLM 厂商：{CURRENT_LLM}")
logger.info(f"数据库：{MYSQL_HOST}:{MYSQL_PORT}")
```

---

### Q4: 多模型配置如何管理？

**方案**：
```python
# 在机器人配置中存储 JSON
chatBotModel.llms_models = {
    "text": {"llms": "DashScope", "modelName": "qwen3-30b"},
    "vl": {"llms": "DashScope", "modelName": "qwen-vl-max"}
}

# 在 ChainModel 中解析
llms, model_name = ChainModel.get_llms_model(chatBotModel, model_type)
```

---

### Q5: 环境切换后需要重启服务吗？

**答**：是的。环境变量在进程启动时加载，需要重启服务才能生效。

---

## 📖 相关文档

- [Python dotenv 文档](https://github.com/theskumar/python-dotenv)
- [Loguru 日志框架](https://github.com/Delgan/loguru)
- [12-Factor App 配置原则](https://12factor.net/zh_cn/config)

---

## 🔗 配置文件引用关系

```
base_config.py（主入口）
  ├─→ base_config_openai.py
  ├─→ base_config_vector.py
  ├─→ test/test_base_config.py
  ├─→ test/test_config_mysql.py
  ├─→ test/test_config_postgres.py
  ├─→ test/test_config_redis.py
  ├─→ prod/prod_base_config.py
  ├─→ prod/prod_config_mysql.py
  ├─→ prod/prod_config_postgres.py
  └─→ prod/prod_config_redis.py

base_config_dashscope.py
  ├─→ base_config_model_type.py
  ├─→ test/test_config_dashscope.py
  └─→ prod/prod_config_dashscope.py

base_config_deepseek.py
  ├─→ test/test_config_deepseek.py
  └─→ prod/prod_config_deepseek.py
```

---

## 📝 配置清单（Checklist）

### 部署前检查

- [ ] 环境变量 `APPLICATION_ENV` 已设置
- [ ] 所有数据库连接信息已配置
- [ ] LLM API Key 已设置（环境变量）
- [ ] 向量库维度与嵌入模型匹配
- [ ] 文件上传路径存在且可写
- [ ] 日志目录存在且可写
- [ ] 定时任务配置符合预期
- [ ] 测试环境和生产环境配置已隔离

### 新增功能检查

- [ ] 新增配置项已添加到 `base_config.py`
- [ ] 测试环境配置已更新
- [ ] 生产环境配置已更新
- [ ] 配置项已添加注释说明
- [ ] 配置变更已记录到文档

---

**文档维护者**：AI 团队  
**最后更新**：2025-12-28
