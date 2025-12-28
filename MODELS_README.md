# Models 目录功能架构文档

> 生成时间：2025-12-28  
> 文档说明：LLM 应用模型层完整架构解析

---

## 📋 概述

这是一个 **LLM 应用的模型层**，采用适配器模式统一管理多厂商 LLM、嵌入模型和向量数据库，为上层业务提供标准化的 AI 能力接口。

---

## 📁 目录结构

```
models/
├── chains/              # 链式调用编排层
│   └── chain_model.py   # LLM 链工厂
├── chatai/              # 聊天模型专用层（流式输出）
│   ├── convert_message.py
│   ├── dashscope/
│   │   └── chat_dashscop.py
│   └── deepseek/
│       └── chat_deepseek.py
├── embeddings/          # 文本嵌入模型层
│   ├── es_model_adapter.py
│   └── dashscope/
│       ├── dashscope_embedding_api.py
│       └── dashscope_embedding_config.py
├── llms/                # 大语言模型适配层
│   ├── llms_adapter.py  # LLM 适配器工厂
│   ├── baidubce/
│   ├── chatglm4/
│   ├── dashscope/
│   ├── deepseek/
│   └── openai/
└── vectordatabase/      # 向量数据库抽象层
    ├── base_vector_client.py
    ├── v_client.py
    ├── vector_postgres_client.py
    └── custom/
        └── custom_pgvector.py
```

---

## 🔧 核心模块详解

### 1. chains/ - 链式调用编排

#### `chain_model.py` - LLM 链工厂

**定位**：基于 LangChain 框架的链式调用工厂类，为医疗问答系统提供统一的对话链构建能力。

**核心方法**：

| 方法 | 返回类型 | 适用场景 |
|------|---------|---------|
| `get_instance()` | `LLMChain` | 常规聊天链，支持历史记忆 |
| `get_instance_stream()` | `RunnableSerializable` | 流式输出的聊天链 |
| `get_chat_instance_stream()` | `RunnableSerializable` | 聊天模型专用流式链，支持角色定义 |
| `get_chat_agent_instance_stream()` | `AgentExecutor` | 集成 Tavily 搜索工具的 Agent |
| `get_document_instance()` | `BaseCombineDocumentsChain` | 文档问答链（RAG 场景） |

**文档问答模式**：
- **Stuff 模式**：将所有文档一次性传给 LLM
- **Refine 模式**：迭代式精炼答案（分批处理大文档）

**内置提示词**：
- `THINKING_PROMPT`：临床医学专业风格（严谨学术）
- `QUICK_QA_PROMPT`：快速问答（≤100字）

**记忆管理**：
- `init_memory()`：构建 `ConversationBufferMemory`，自动倒序处理历史数据

---

### 2. llms/ - 大语言模型适配层

#### `llms_adapter.py` - LLM 适配器工厂

**职责**：根据配置动态选择厂商模型，屏蔽不同 LLM 厂商差异。

**核心方法**：
- `get_model_instance()` - 获取普通 LLM 实例（用于 `LLMChain`）
- `get_chat_model_instance()` - 获取聊天模型实例（用于流式对话）

**支持的厂商实现**（继承 LangChain 的 `LLM` 基类）：

| 子目录 | 文件 | 厂商 | 核心功能 |
|--------|------|------|---------|
| `dashscope/` | `dashscope.py` | 阿里百炼 | 支持多模态（文本/视觉）、工具调用、流式推理 |
| `deepseek/` | `deepseek.py` | DeepSeek | 基础文本推理 |
| `openai/` | `chatopenai.py` | OpenAI | GPT 系列模型 |
| `chatglm4/` | `chatglm4.py` | 智谱 | ChatGLM4 模型 |
| `baidubce/` | `baidubce.py` | 百度智能云 | 文心系列 |

**示例代码**：
```python
adapter = LLMsAdapter(model="DashScope", model_name="qwen-max")
llm = adapter.get_model_instance(history=history, question=question)
```

---

### 3. chatai/ - 聊天模型专用层

**用途**：用于需要 **流式输出** 和 **消息格式标准化** 的场景。

#### `convert_message.py` - 消息转换器

**核心类**：`MessageChunkConverter`

**功能**：
- 将流式 chunk 转换为 LangChain 的 `ChatGenerationChunk`
- 处理思维链（reasoning_content）
- 统一 OpenAI 格式消息
- 支持 token 使用量统计（`UsageMetadata`）

**关键方法**：
- `convert_chunk_to_generation_chunk()` - Chunk 转换
- `convert_input()` - 输入格式转换

#### 厂商实现（继承 `BaseChatModel`）

| 文件 | 功能 |
|------|------|
| `dashscope/chat_dashscop.py` | 百炼聊天模型，支持流式、异步、工具调用 |
| `deepseek/chat_deepseek.py` | DeepSeek 聊天模型 |

**与 llms/ 的区别**：
- `llms/` 实现 `LLM` 接口（适用于 `LLMChain`）
- `chatai/` 实现 `BaseChatModel` 接口（适用于 `ChatPromptTemplate` + 流式输出）

---

### 4. embeddings/ - 文本嵌入模型

**用途**：向量化文本，支持 RAG（检索增强生成）场景。

#### `es_model_adapter.py` - 嵌入模型适配器

**支持的模型**：
- OpenAI Embeddings（`text-embedding-ada-002`）
- DashScope Embeddings（阿里百炼）

**示例代码**：
```python
adapter = EmbeddingsModelAdapter()
embeddings = adapter.get_model_instance(model="DashScope")
```

#### 厂商实现

| 文件 | 功能 |
|------|------|
| `dashscope/dashscope_embedding_api.py` | 阿里百炼嵌入模型实现 |
| `dashscope/dashscope_embedding_config.py` | 百炼嵌入配置参数 |

---

### 5. vectordatabase/ - 向量数据库抽象层

**用途**：统一向量库操作接口，当前仅支持 PostgreSQL + pgvector。

#### `base_vector_client.py` - 抽象基类

**定义接口**：
- `delete_data()` - 删除向量数据
- `delete_file_data()` - 按文件 ID 删除
- `query_data()` - 查询向量数据
- `query_page_data()` - 分页查询向量数据
- `update_data()` - 更新向量数据

#### `v_client.py` - 工厂函数

**功能**：根据配置返回对应向量库客户端实例

```python
from models.vectordatabase.v_client import get_instance_client

vector_client = get_instance_client()  # 返回 VectorPostgresClient 实例
```

#### 实现类

| 文件 | 功能 |
|------|------|
| `vector_postgres_client.py` | PostgreSQL 向量库实现 |
| `custom/custom_pgvector.py` | 自定义 pgvector 扩展（ORM 模型） |

---

## 🎯 设计模式解析

### 1. 适配器模式（Adapter Pattern）

所有 `*_adapter.py` 文件屏蔽厂商差异：

```
业务层 → LLMsAdapter → [DashScope | DeepSeek | OpenAI ...]
       → EmbeddingsModelAdapter → [OpenAI Embeddings | DashScope Embeddings]
       → VectorClient → [Postgres | Pinecone ...]
```

**优势**：
- 切换厂商只需修改配置，无需改动业务代码
- 统一接口降低学习成本
- 方便扩展新厂商

### 2. 工厂模式（Factory Pattern）

- `ChainModel` - 链工厂，根据场景返回不同链类型
- `v_client.get_instance_client()` - 向量库工厂
- `LLMsAdapter.get_model_instance()` - LLM 工厂

### 3. 分层解耦

```
┌─────────────────────────┐
│ chains/ (编排层)         │ ← 组装 Prompt + LLM + Memory
├─────────────────────────┤
│ llms/chatai/ (模型层)    │ ← 封装厂商 API
├─────────────────────────┤
│ embeddings/ (嵌入层)     │ ← 文本向量化
├─────────────────────────┤
│ vectordatabase/ (存储层) │ ← 向量持久化
└─────────────────────────┘
```

---

## 💡 关键技术特性

### 1. 多模态支持
- DashScope 支持文本+图像输入（`MODEL_TYPE_VL`）
- 通过 `images` 参数传递图片 URL

### 2. 流式输出
- 所有聊天模型支持 `_stream()` 方法
- 使用 `ChatGenerationChunk` 实现渐进式响应

### 3. 历史记忆管理
- 通过 `history` 参数传递历史对话
- `ConversationBufferMemory` 实现长程记忆
- 自动倒序处理历史数据

### 4. 工具调用（Function Calling）
- 支持 LangChain 的 Agent 工具调用
- 集成 Tavily 搜索（`get_chat_agent_instance_stream`）
- 最大迭代次数 3 次

### 5. 思维链（Chain of Thought）
- `convert_message.py` 专门处理推理过程（`reasoning_content`）
- 支持思维模式切换（`enable_thinking`）

### 6. 提示词动态切换
- 通过 `kwargs` 标志动态替换提示词
- `enable_thinking` - 启用临床医学专业模式
- `enable_quick_qa` - 启用快速问答模式

---

## 🔄 典型调用流程

### 场景 1：常规聊天

```python
from models.chains.chain_model import ChainModel
from service.domain.ai_chat_bot import ChatBotModel

# 1. 构建聊天链
chain = ChainModel.get_instance(
    question="什么是高血压？",
    chatBotModel=chatBotModel,
    history=history
)

# 2. 执行推理
response = chain.run(question="什么是高血压？")
```

### 场景 2：流式聊天

```python
# 1. 构建流式链
chain = ChainModel.get_chat_instance_stream(
    chatBotModel=chatBotModel,
    history=history,
    model_type=MODEL_TYPE_TEXT
)

# 2. 流式输出
for chunk in chain.stream({"question": "什么是糖尿病？"}):
    print(chunk.content, end="", flush=True)
```

### 场景 3：文档问答（RAG）

```python
# 1. 构建文档链
doc_chain = ChainModel.get_document_instance(
    question="这篇论文的主要结论是什么？",
    chatBotModel=chatBotModel,
    history=history,
    has_chunk=True
)

# 2. 传入文档执行推理
response = doc_chain.run(
    input_documents=documents,
    question="这篇论文的主要结论是什么？"
)
```

### 场景 4：Agent 工具调用

```python
# 1. 构建 Agent 执行器
agent = ChainModel.get_chat_agent_instance_stream(
    chatBotModel=chatBotModel,
    history=history
)

# 2. 执行（自动调用搜索工具）
response = agent.invoke({
    "question": "2024年诺贝尔医学奖获得者是谁？",
    "chat_history": "",
    "files_context": ""
})
```

---

## 📊 配置依赖关系

### 配置文件引用

```
models/
├── chains/chain_model.py
│   ├── config.base_config → TAVILY_API_KEY, DEFAULT_CHAT_BOT_ROLE
│   ├── config.base_config_model_type → MODEL_TYPE_TEXT
│   └── content.prompt_template_chat → CONVERSATION_CHAT_TEMPLATE
│
├── llms/llms_adapter.py
│   ├── config.base_config → CURRENT_LLM, OPENAI_MODEL_NAME
│   ├── config.base_config_dashscope → BASHSCOPE_*
│   └── config.base_config_deepseek → DEEPSEEK_MODEL_NAME
│
└── embeddings/es_model_adapter.py
    └── config.base_config → VECTOR_EMBEDDINGS_MODEL
```

### 业务实体依赖

```
models/ → service.domain.ai_chat_bot → ChatBotModel
       → service.domain.ai_chat_history → ChatHistoryModel
       → service.namespacefile.namespace_file_metadata → MetadataModel
```

---

## 🚀 扩展指南

### 新增 LLM 厂商

1. 在 `models/llms/` 下创建厂商目录，如 `anthropic/`
2. 实现继承自 `LLM` 的模型类
3. 在 `llms_adapter.py` 的 `get_model_instance()` 中添加分支
4. 在配置文件中添加相应配置项

### 新增向量数据库

1. 在 `models/vectordatabase/` 下创建实现类
2. 继承 `BaseVectorClient` 并实现所有抽象方法
3. 在 `v_client.py` 的 `get_instance_client()` 中添加分支

### 新增嵌入模型

1. 在 `models/embeddings/` 下创建厂商目录
2. 实现 LangChain 的 `Embeddings` 接口
3. 在 `es_model_adapter.py` 的 `get_model_instance()` 中添加分支

---

## ⚠️ 注意事项

### 1. DashScope 特殊处理
在多处对 DashScope 做特殊判断（清空 memory），可能因其原生支持历史记录管理。

### 2. 历史记录格式
- LangChain Memory 格式：`ConversationBufferMemory`
- ChatGLM 格式：`[[Q1, A1], [Q2, A2]]`
- 需要同时维护两种格式

### 3. 模型类型区分
- `MODEL_TYPE_TEXT` - 纯文本模型
- `MODEL_TYPE_VL` - 视觉语言模型（支持图像输入）

### 4. 流式输出处理
- 使用 `_stream()` 方法返回 `Iterator[ChatGenerationChunk]`
- 需正确处理 `reasoning_content`（思维链）

---

## 📖 相关文档

- [LangChain 官方文档](https://python.langchain.com/)
- [阿里百炼 API 文档](https://help.aliyun.com/zh/model-studio/)
- [DeepSeek API 文档](https://platform.deepseek.com/docs)
- [pgvector 使用指南](https://github.com/pgvector/pgvector)

---

## 🔍 常见问题

### Q1: 如何切换 LLM 厂商？
A: 修改配置文件中的 `CURRENT_LLM` 参数，或在调用时指定 `model` 参数。

### Q2: Stuff 和 Refine 模式如何选择？
A: 
- 文档较小（< 4K tokens）→ Stuff 模式（一次性处理）
- 文档较大 → Refine 模式（迭代式处理，但耗时更长）

### Q3: 如何启用思维链模式？
A: 在调用时传入 `enable_thinking=True` 参数。

### Q4: 为什么有 llms/ 和 chatai/ 两个目录？
A: 
- `llms/` - 实现 `LLM` 接口，适用于传统链式调用
- `chatai/` - 实现 `BaseChatModel` 接口，适用于流式对话和工具调用

---

**文档维护者**：AI 团队  
**最后更新**：2025-12-28
