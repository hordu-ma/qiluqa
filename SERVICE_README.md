# Service 目录功能架构文档

> 生成时间：2025-12-28  
> 文档说明：医疗问答系统业务服务层完整架构解析

---

## 📋 概述

这是一个 **医疗问答系统的业务服务层**，实现了公共问答、领域知识问答、知识库管理、文件处理等核心业务逻辑。采用领域驱动设计（DDD），将业务逻辑、数据模型、定时任务分层管理。

---

## 📁 目录结构

```
service/
├── 核心业务服务层
│   ├── base_chat_message.py        # 聊天消息基础处理类
│   ├── base_compose_bot.py         # 机器人组合基类
│   ├── bot_service.py               # 机器人初始化服务
│   ├── chat_private_service.py      # 领域知识问答服务（RAG）
│   ├── chat_public_service.py       # 公共知识问答服务
│   ├── chat_response.py             # 响应模型定义
│   ├── intention_recognition.py     # 意图识别服务
│   ├── local_repo_service.py        # 本地知识库管理
│   ├── map_reduce_summarizer.py     # MapReduce 文档摘要
│   ├── medical_question_optimizer.py # 医学问题优化器
│   └── search_service.py            # 搜索服务（Tavily）
│
├── domain/                          # 领域模型层（数据实体）
│   ├── ai_chat_bot.py               # 机器人实体模型
│   ├── ai_chat_history.py           # 聊天历史实体模型
│   ├── ai_namespace.py              # 知识库实体模型
│   ├── ai_namespace_file.py         # 知识库文件实体模型
│   ├── ai_bot_namespace_relation.py # 机器人与知识库关系
│   ├── ai_chat_images.py            # 聊天图片实体
│   ├── ai_disclaimer.py             # 免责声明实体
│   ├── ai_prohibited.py             # 违禁词实体
│   └── ...                          # 其他实体模型
│
├── namespacefile/                   # 知识库文件管理
│   ├── namespace_file_service.py    # 知识库文件服务
│   ├── namespace_file_request.py    # 请求模型
│   ├── namespace_file_response.py   # 响应模型
│   ├── namespace_file_metadata.py   # 文件元数据
│   └── ...
│
└── schedule/                        # 定时任务/调度器
    ├── namespace_file_schedule.py   # 文件处理调度
    ├── disclaimer_data_schedule.py  # 免责声明数据调度
    ├── prohibited_data_schedule.py  # 违禁词数据调度
    └── spider_network_schedule.py   # 网络爬虫调度
```

---

## 🎯 核心业务服务

### 1. 聊天问答服务

#### 1.1 `chat_public_service.py` - 公共知识问答

**定位**：无需知识库的通用医学问答服务。

**核心方法**：
- `ask()` - 普通问答（非流式）
- `ask_stream()` - 流式问答
- `ask_agent_stream()` - Agent 模式问答（支持工具调用）

**流程特性**：
```
用户提问
  ↓
意图识别（MedicalDiagnosisChecker）
  ↓ (非医学问题直接返回固定话术)
问题优化（MedicalQuestionOptimizer）
  ↓
处理附件（图片 OCR/文件摘要）
  ↓
构建 Prompt（动态占位符替换）
  ↓
调用 LLM 链（支持思维链/快速问答模式）
  ↓
流式返回结果
```

**特色功能**：
- **意图识别**：过滤非医学问题，返回固定话术
- **问题优化**：将简单问题扩展为专业医学问题
- **附件处理**：
  - 图片 → OCR 识别 + Vision 模型分析
  - 文件 → MapReduce 摘要（支持并行处理）
- **思维链模式**：`enable_thinking=True` 启用推理过程展示
- **快速问答模式**：`enable_quick_qa=True` 限制回答字数（≤100字）

---

#### 1.2 `chat_private_service.py` - 领域知识问答（RAG）

**定位**：基于私有知识库的检索增强生成（RAG）问答。

**核心方法**：
- `ask()` - 普通问答
- `ask_stream()` - 流式问答

**RAG 流程**：
```
用户提问
  ↓
查询机器人关联的知识库
  ↓
向量检索（top_k 相似分片）
  ↓
重排序（Rerank）
  ↓
构建 Context（分片内容 + 图表标签）
  ↓
调用文档链（Stuff/Refine 模式）
  ↓
返回答案 + 溯源信息（metadata）
```

**溯源机制**：
- 返回召回分片的元数据（文件名、匹配度、内容、图表）
- 支持图表标签嵌入（`CHUNK_IMAGE_LABELS`）

---

### 2. 知识库管理服务

#### 2.1 `local_repo_service.py` - 本地知识库管理

**定位**：处理文件上传、分片、向量化、存储的完整流程。

**核心方法**：
- `push()` - 推送文件到知识库
- `loader()` - 文件加载（支持 PDF/HTML/TXT）
- `ocr_picture_txt()` - 图片 OCR 识别
- `query()` - 向量检索
- `delete()` - 删除知识库数据

**文件处理流程**：
```
上传文件
  ↓
文件加载（DirectoryLoader/PyPDFLoader）
  ↓
特殊处理（保险单 OCR）
  ↓
分片策略（AiChunkStrategyDomain 动态选择）
  ↓
向量化（EmbeddingsModelAdapter）
  ↓
存储到向量库（PostgreSQL + pgvector）
  ↓
返回分片 IDs
```

**支持的文件类型**：
- PDF（`PyPDFLoader`）
- HTML（`UnstructuredHTMLLoader`）
- TXT/MD（`TextLoader`）

**分片策略**：
- 按文件配置动态选择（`AiChunkStrategyDomain.switch_case_by_chunk_strategy`）
- 支持自定义 `chunk_size` 和 `chunk_overlap`

---

#### 2.2 `namespacefile/namespace_file_service.py` - 知识库文件服务

**定位**：知识库文件的 CRUD 管理和分片查询。

**核心方法**：
- `query_chunk_page()` - 分片分页查询
- `modify_chunk()` - 修改分片内容
- `modify_chunk_status()` - 修改分片状态
- `spider_url()` - 爬取网页并入库

**爬虫功能**：
- 支持网页内容爬取（`BeautifulSoup`）
- 自动提取正文内容
- 自动向量化并入库

---

### 3. 辅助服务

#### 3.1 `intention_recognition.py` - 意图识别

**定位**：判断用户问题是否属于医学领域。

**核心类**：
- `LLMIntentClassifier` - 基于 LLM 的意图分类器
- `MedicalDiagnosisChecker` - 医疗诊断检查器

**识别逻辑**：
```python
class MedicalDiagnosisChecker:
    FIXED_RESPONSE = "医知立方聚焦医学答疑，请提问医学及生命科学相关问题"
    
    def check_medical_intent(user_input: str) -> bool:
        # 返回 True（医学相关） 或 False（非医学）
```

**判断标准**：
- **医学相关**：疾病诊疗、医学术语、药物咨询、医保政策等
- **非医学相关**：闲聊、购物、法律、教育等

---

#### 3.2 `medical_question_optimizer.py` - 医学问题优化器

**定位**：将简单问题扩展为专业、全面的医学问题。

**优化策略**：
```
原始问题："咳嗽怎么办？"
  ↓
优化后："想问问什么原因会导致咳嗽，需要与何种疾病鉴别，该怎么处理？"
```

**优化原则**：
1. **聚焦医学场景**：围绕疾病症状、检查报告、用药咨询等
2. **用户视角表述**：模拟真实咨询场景
3. **信息补充原则**：
   - 症状类 → 仅提及"出现症状"，不追问细节
   - 报告类 → 仅说明"有一份医学报告"，不指定类型
   - 学习类 → 保留"医学"整体范畴，不限定具体学科
   - 用药类 → 仅提及"有用药需求"，不预设病情
4. **保留原始指令**：严格保留字数限制、格式要求等显性指令

---

#### 3.3 `map_reduce_summarizer.py` - MapReduce 文档摘要

**定位**：对大文件进行分块并行摘要，最后汇总。

**处理流程**：
```
多个文件
  ↓
并行处理（ThreadPoolExecutor）
  ↓ 每个文件：
    分块（CharacterTextSplitter）
    ↓
    迭代摘要（Map 阶段）
      existing_content + 新 chunk → 新 summary
    ↓
    返回文件摘要
  ↓
汇总所有文件摘要（Reduce 阶段）
  ↓
最终总结
```

**参数配置**：
- `CHUNK_SIZE = 1024 * 20`（20KB）
- `word_limit`：每次摘要最大字数
- `max_workers`：并发处理线程数

---

#### 3.4 `search_service.py` - 搜索服务

**定位**：集成 Tavily 搜索 API，提供实时网络搜索能力。

**核心方法**：
```python
def get_tavily_search_list(query: str):
    # 返回搜索结果列表（content + url）
```

**应用场景**：
- Agent 模式自动调用（`get_chat_agent_instance_stream`）
- 实时信息查询（如"今天天气""最新新闻"）

---

### 4. 基础服务

#### 4.1 `base_chat_message.py` - 聊天消息基础处理

**定位**：所有聊天服务的抽象基类，提供通用方法。

**核心方法**：
- `placeholder()` - 动态占位符替换
- `query_chat_history()` - 查询历史聊天记录
- `get_metadata_list()` - 提取分片元数据
- `get_label_content()` - 封装图表标签
- `save_chat_history()` - 保存聊天记录

**占位符机制**：
```python
# Prompt 中的占位符格式：
{business.user_name}  # 业务占位符
{system.current_date} # 系统占位符

# 自动替换：
prompt = "{business.user_name}，今天是{system.current_date}"
→ "张三，今天是2025-12-28"
```

**历史记录管理**：
- 支持按用户/机器人/分组查询
- 限制记忆轮数（`memory_limit_size`）
- 过滤敏感内容（`filter_history_list`）

---

#### 4.2 `bot_service.py` - 机器人初始化服务

**定位**：系统启动时自动初始化预制机器人。

**核心方法**：
```python
def init_bot_list():
    # 从 prompt_template_list 批量创建机器人
```

**应用场景**：
- 系统部署时初始化默认机器人
- 自动创建多个专科问答机器人（如内科、外科等）

---

## 📦 领域模型层（Domain）

### 核心实体模型

| 实体 | 文件 | 功能 |
|------|------|------|
| **机器人** | `ai_chat_bot.py` | 存储机器人配置（Prompt、模型、记忆轮数等） |
| **聊天历史** | `ai_chat_history.py` | 存储问答记录（问题、答案、评价、思维链等） |
| **知识库** | `ai_namespace.py` | 知识库配置（分片策略、类型、用户归属） |
| **知识库文件** | `ai_namespace_file.py` | 文件信息（路径、状态、向量化进度） |
| **机器人-知识库关系** | `ai_bot_namespace_relation.py` | 多对多关系映射 |
| **图片信息** | `ai_chat_images.py` | 聊天中的图片记录 |
| **免责声明** | `ai_disclaimer.py` | 医疗免责声明文本 |
| **违禁词** | `ai_prohibited.py` | 敏感词过滤 |

---

### 实体模型设计模式

**示例：`ChatBotModel`**

```python
class ChatBotModel:
    # 常量定义
    CONSTANTS_BOT_MASTER = "Master"  # 主机器人
    CONSTANTS_BOT_SLAVER = "Slave"   # 从机器人
    CONSTANTS_PRIVATE_BOT = 0        # 领域问答机器人
    CONSTANTS_PUBLIC_BOT = 1         # 公共问答机器人
    
    # 核心属性
    bot_id: str          # 业务标识
    prompt: str          # 提示词模板
    llms: str            # 使用的 LLM 厂商
    vector_top_k: int    # 召回分片数量
    memory_limit_size: int  # 记忆轮数限制
    
    # 业务方法
    def is_public_bot(self) -> bool:
        return self.use_type == self.CONSTANTS_PUBLIC_BOT
    
    def get_llm_model_name(self) -> str:
        # 动态获取模型名称
```

**ORM 模式**：
- 每个实体对应一张数据库表
- 包含 Domain 类（业务逻辑层）
- 提供 CRUD 方法（`create`/`find_one`/`update`/`delete`）

---

## 🔄 业务流程详解

### 流程 1：公共问答（流式）

```
┌─────────────────────────────────────────────────────┐
│ 1. 接收用户请求                                       │
│    - question: "高血压怎么治疗？"                      │
│    - bot_id: "public_bot_001"                        │
│    - files: [图片1.jpg, 报告.pdf]                    │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 2. 意图识别（MedicalDiagnosisChecker）                │
│    - 判断是否医学问题 → True（继续）                   │
│    - 非医学问题 → 返回固定话术                         │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 3. 问题优化（MedicalQuestionOptimizer）               │
│    - 原问题："高血压怎么治疗？"                        │
│    - 优化后："高血压的治疗方法有哪些？包括药物治疗、   │
│      非药物治疗的具体方案和注意事项？"                 │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 4. 附件处理（并行）                                   │
│    ┌─────────────┐      ┌─────────────┐             │
│    │ 图片 OCR    │      │ 文件摘要    │             │
│    │ + Vision AI │      │ (MapReduce) │             │
│    └─────────────┘      └─────────────┘             │
│         ↓                      ↓                     │
│    图片描述文本          文件关键内容                 │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 5. 构建完整 Prompt                                    │
│    - 系统角色（bot_role）                             │
│    - 历史对话（memory）                               │
│    - 优化后的问题                                     │
│    - 附件上下文（图片描述 + 文件摘要）                 │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 6. 调用 LLM 链（流式）                                │
│    - 模式选择：                                       │
│      • 普通模式（默认）                               │
│      • 思维链模式（enable_thinking=True）             │
│      • 快速问答（enable_quick_qa=True）               │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 7. 流式返回                                           │
│    - 逐 token 返回（yield）                           │
│    - 包含思维过程（reasoning_content）                │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 8. 保存聊天记录                                       │
│    - 问题、答案、思维链、附件信息                      │
└─────────────────────────────────────────────────────┘
```

---

### 流程 2：领域问答（RAG）

```
┌─────────────────────────────────────────────────────┐
│ 1. 接收用户请求                                       │
│    - question: "公司保险理赔流程是什么？"              │
│    - bot_id: "insurance_bot_001"                     │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 2. 查询机器人配置                                     │
│    - 关联知识库：[保险知识库_001]                     │
│    - vector_top_k: 5                                 │
│    - chains_chunk_type: "stuff"                      │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 3. 向量检索（LocalRepositoryDomain.query）           │
│    - 将问题向量化                                     │
│    - 在知识库中检索 top_k 相似分片                     │
│    - 返回：[(分片1, 0.95), (分片2, 0.89), ...]        │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 4. 重排序（Rerank - 可选）                            │
│    - 使用更精细的模型重新排序                          │
│    - 过滤低相关度分片                                 │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 5. 构建 Context                                       │
│    - 分片内容拼接                                     │
│    - 附加图表标签（get_label_content）                │
│    - 元数据提取（文件名、页码、匹配度）                │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 6. 调用文档链                                         │
│    - Stuff 模式：一次性传入所有分片                   │
│    - Refine 模式：迭代式处理每个分片                  │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 7. 返回答案 + 溯源信息                                │
│    - answer: "理赔流程包括以下步骤..."               │
│    - metadata: [                                     │
│        {name: "理赔手册.pdf", score: 0.95, ...},     │
│        {name: "保险条款.pdf", score: 0.89, ...}      │
│      ]                                               │
└─────────────────────────────────────────────────────┘
```

---

### 流程 3：文件上传与向量化

```
┌─────────────────────────────────────────────────────┐
│ 1. 上传文件                                           │
│    - file_path: "保险条款.pdf"                        │
│    - namespace_id: "insurance_001"                   │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 2. 文件加载（LocalRepositoryDomain.loader）          │
│    - PDF → PyPDFLoader                               │
│    - HTML → UnstructuredHTMLLoader                   │
│    - TXT → TextLoader                                │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 3. 特殊处理（可选）                                   │
│    - 保险单图片 → OCR 识别（pytesseract）            │
│    - 提取表格数据                                     │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 4. 分片策略（AiChunkStrategyDomain）                 │
│    - 根据文件配置选择策略                             │
│    - RecursiveCharacterTextSplitter（默认）          │
│    - 自定义分片规则                                   │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 5. 向量化（EmbeddingsModelAdapter）                  │
│    - 调用嵌入模型（DashScope/OpenAI）                │
│    - 生成每个分片的向量                               │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 6. 存储到向量库（VectorPostgresClient）              │
│    - 插入分片文本                                     │
│    - 插入向量（pgvector）                            │
│    - 保存元数据（文件名、页码、图表等）                │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 7. 返回分片 IDs                                       │
│    - ids: ["chunk_001", "chunk_002", ...]            │
└─────────────────────────────────────────────────────┘
```

---

## 🎨 设计模式与架构特点

### 1. 分层架构

```
┌─────────────────────────────────────────────┐
│ API 层（FastAPI）                            │
│ - 接收 HTTP 请求                             │
│ - 参数验证                                   │
└─────────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────────┐
│ Service 层（业务逻辑）                        │
│ - chat_public_service.py                    │
│ - chat_private_service.py                   │
│ - local_repo_service.py                     │
└─────────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────────┐
│ Domain 层（领域模型）                         │
│ - ChatBotModel                              │
│ - NamespaceModel                            │
│ - ChatHistoryModel                          │
└─────────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────────┐
│ Infrastructure 层（基础设施）                 │
│ - models/ (LLM 适配器)                      │
│ - framework/ (工具类)                       │
│ - MySQL / PostgreSQL                        │
└─────────────────────────────────────────────┘
```

---

### 2. 模板方法模式

**`BaseChatMessage` 作为抽象基类**：

```python
class BaseChatMessage:
    # 模板方法
    def query_chat_history(self, user_id, bot_id):
        # 通用历史查询逻辑
    
    def save_chat_history(self, question, answer):
        # 通用保存逻辑

class ChatPublicDomain(BaseChatMessage):
    # 实现具体业务逻辑
    def ask_stream(self, question):
        history = self.query_chat_history(...)  # 复用基类方法
        # 公共问答逻辑
        self.save_chat_history(...)  # 复用基类方法

class ChatPrivateDomain(BaseChatMessage):
    # 实现具体业务逻辑
    def ask_stream(self, question):
        history = self.query_chat_history(...)  # 复用基类方法
        # RAG 问答逻辑
        self.save_chat_history(...)  # 复用基类方法
```

---

### 3. 策略模式

**分片策略动态选择**：

```python
class AiChunkStrategyDomain:
    def switch_case_by_chunk_strategy(self, namespaceFileModel, docs):
        # 根据文件配置选择不同分片策略
        if strategy == "recursive":
            return RecursiveCharacterTextSplitter(...)
        elif strategy == "character":
            return CharacterTextSplitter(...)
        elif strategy == "custom":
            return CustomSplitter(...)
```

---

### 4. 工厂模式

**响应模型工厂**：

```python
class ChatResponse:
    @staticmethod
    def success(data):
        return QueryResponse(code=200, data=data)
    
    @staticmethod
    def error(code, message):
        return QueryResponse(code=code, message=message)
```

---

## 💡 核心技术特性

### 1. 流式输出（Streaming）

**实现方式**：
```python
async def ask_stream(self, question: str):
    chain = ChainModel.get_chat_instance_stream(...)
    
    async for chunk in chain.astream({"question": question}):
        if isinstance(chunk, AIMessageChunk):
            yield chunk.content  # 逐 token 返回
```

**应用场景**：
- 长文本生成（避免用户等待）
- 思维链展示（实时显示推理过程）

---

### 2. 并行处理（Concurrency）

**MapReduce 摘要并行**：
```python
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(process_file, file) 
        for file in files
    ]
    results = [future.result() for future in futures]
```

**性能优化**：
- 多文件并行处理（4 线程）
- 单文件内分块串行（保证上下文连贯）

---

### 3. 动态 Prompt 组装

**占位符替换机制**：
```python
prompt = """
你好，{business.user_name}！
今天是{system.current_date}。
你的会员等级是{business.vip_level}。
"""

# 自动替换
BaseChatMessage.placeholder(
    chatBotModel=chatBotModel,
    user_name="张三",
    current_date="2025-12-28",
    vip_level="黄金"
)

# 结果：
# 你好，张三！
# 今天是2025-12-28。
# 你的会员等级是黄金。
```

---

### 4. 意图识别 + 问题优化（两阶段）

```
原始问题："咳嗽"
    ↓
【阶段 1：意图识别】
LLMIntentClassifier → "medical_diagnosis"（通过）
    ↓
【阶段 2：问题优化】
MedicalQuestionOptimizer → "想问问什么原因会导致咳嗽，需要与何种疾病鉴别，该怎么处理？"
    ↓
传递给 LLM 进行推理
```

---

### 5. 图表标签嵌入（Vision 增强）

**处理流程**：
```python
# 1. 检索分片时携带图表元数据
metadata = {
    "images": [
        {"name": "图1.png", "mark_num": "1", "page_num": "3"}
    ]
}

# 2. 生成 Markdown 标签
label = "![表1](http://host/图1.png)"

# 3. 嵌入 Prompt
context = f"{分片文本}\n\n{label}"
```

**应用场景**：
- 医学影像报告解读
- 检验报告数值分析
- 图文混排内容问答

---

## 📊 数据流转图

### 公共问答数据流

```
用户 → API → ChatPublicDomain
              ↓
         MedicalDiagnosisChecker（意图识别）
              ↓
         MedicalQuestionOptimizer（问题优化）
              ↓
         附件处理（OCR + 摘要）
              ↓
         ChainModel（构建链）
              ↓
         LLMsAdapter（调用 LLM）
              ↓
         流式返回（yield chunk）
              ↓
         保存历史（AiChatHistoryDomain）
              ↓
         返回响应 → 用户
```

---

### 领域问答数据流（RAG）

```
用户 → API → ChatPrivateDomain
              ↓
         查询机器人配置（AiChatBotDomain）
              ↓
         查询关联知识库（AiBotNamespaceRelationDomain）
              ↓
         向量检索（LocalRepositoryDomain.query）
              ↓
         PostgreSQL + pgvector（余弦相似度搜索）
              ↓
         返回 top_k 分片 + metadata
              ↓
         构建 Context（分片拼接 + 图表标签）
              ↓
         调用文档链（Stuff/Refine）
              ↓
         返回答案 + 溯源信息 → 用户
```

---

## 🚀 扩展指南

### 新增问答模式

1. 在 `service/` 下创建新服务类，继承 `BaseChatMessage`
2. 实现 `ask()` 和 `ask_stream()` 方法
3. 在 `models/chains/chain_model.py` 中添加对应链构建方法
4. 更新 API 路由

---

### 新增文件类型支持

1. 在 `LocalRepositoryDomain.loader()` 中添加新的 Loader
2. 配置文件扩展名映射
3. 添加特殊处理逻辑（如 OCR、表格提取）

---

### 新增定时任务

1. 在 `service/schedule/` 下创建新的调度器
2. 实现任务逻辑
3. 在主程序中注册定时任务

---

## ⚠️ 注意事项

### 1. 意图识别性能优化

- 当前每次问答都调用 LLM 判断意图，成本较高
- 建议：使用轻量级分类模型（如 DistilBERT）或规则引擎

### 2. 向量检索优化

- 当前使用余弦相似度，对长文本效果有限
- 建议：引入混合检索（向量 + BM25）或 Rerank 模型

### 3. 并发控制

- MapReduce 摘要并发数固定为 4
- 建议：根据服务器资源动态调整

### 4. 历史记忆管理

- 当前全量加载历史记录到 Memory
- 建议：大量历史记录场景下使用滑动窗口或摘要

### 5. 图表处理

- 当前仅支持 Markdown 图片标签
- 建议：支持表格、公式等更多格式

---

## 🔍 常见问题

### Q1: 如何切换问答模式？
A: 通过 `bot_id` 区分，机器人配置中 `use_type` 字段决定：
- `0` - 领域问答（私有知识库）
- `1` - 公共问答（无知识库）

### Q2: 如何启用思维链模式？
A: 在调用时传入 `enable_thinking=True`，会切换到思维链专用模型和 Prompt。

### Q3: 如何调整召回分片数量？
A: 修改机器人配置中的 `vector_top_k` 字段（默认 5）。

### Q4: 如何处理超大文件？
A: 
- 使用 Refine 模式（`chains_chunk_type="refine"`）
- 增大 `chunk_size`（如 2048）
- 使用 MapReduce 摘要预处理

### Q5: 如何实现多知识库检索？
A: `AiBotNamespaceRelationDomain` 支持一个机器人关联多个知识库，检索时会合并结果。

---

## 📖 相关文档

- [LangChain 官方文档](https://python.langchain.com/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [pgvector 使用指南](https://github.com/pgvector/pgvector)
- [Tavily Search API](https://tavily.com/)

---

## 🔗 与其他模块的集成

### 依赖关系

```
service/
  ├─→ models/          # LLM 适配器、向量库客户端
  ├─→ config/          # 配置参数
  ├─→ content/         # Prompt 模板
  ├─→ framework/       # 业务异常、工具类
  └─→ custom/          # 定制化业务（安利、bespin 等）
```

---

**文档维护者**：AI 团队  
**最后更新**：2025-12-28
