import json
from typing import List, Any

from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.base_language import BaseLanguageModel
from langchain.chains.combine_documents.base import BaseCombineDocumentsChain
from langchain.chains.question_answering import load_qa_chain
from langchain_community.tools import TavilySearchResults
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSerializable
from loguru import logger
from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate, \
    SystemMessagePromptTemplate
from langchain.memory import ConversationBufferMemory

from config.base_config import TAVILY_API_KEY, DEFAULT_CHAT_BOT_ROLE
from config.base_config_model_type import MODEL_TYPE_TEXT
from framework.business_code import ERROR_10002
from framework.business_except import BusinessException
from models.llms.dashscope.dashscope import DashScopeAI
from models.llms.llms_adapter import LLMsAdapter
from content.prompt_template_chat import (
    MEMORY_HISTORY_KEY,
    MEMORY_INPUT_KEY,
    CONVERSATION_CHAT_TEMPLATE,
    CONVERSATION_CHAT_VARIABLES
)
from service.domain.ai_chat_bot import ChatBotModel
from service.domain.ai_chat_history import ChatHistoryModel

THINKING_PROMPT = """你是一名临床医学专业人士，请严格按以下要求回答医学问题：
1. 回答风格：严谨、学术，语言简明，避免口语化，类似医学教科书或科研综述。
2. 输出内容：仅针对用户输入中的医学范畴内容应答，非医学信息直接过滤。输出结构和逻辑清晰。

现在，请回答以下问题：
<历史聊天记录>{chat_history}</历史聊天记录>
<用户问题>{question}</用户问题>
<附件信息>{files_context}</附件信息>"""

QUICK_QA_PROMPT = """<历史聊天记录>{chat_history}</历史聊天记录>

<用户问题>{question}</用户问题>

<附件信息>{files_context}</附件信息>
输出要求：请用不超过100字回答问题！"""


class ChainModel:
    """
    链式模型
        - 可提供默认常规的聊天链实例对象
        - 可提供语义搜索的聊天链实例对象
    """

    @classmethod
    def get_instance(
            cls,
            question: str,
            chatBotModel: ChatBotModel,
            history: List[ChatHistoryModel] = None,
            verbose: bool = True,
            **kwargs,
    ) -> LLMChain:
        """
        获取默认的聊天链实例对象
        :param question: 用户问题
        :param chatBotModel: 机器人实体对象
        :param history: 历史聊天记录
        :param verbose: 过程冗余信息
        :param kwargs: 扩展参数
        :return: 聊天链实例对象
        """
        # 封装历史聊天记录
        memory, chat_glm_history = cls.init_memory(history=history)
        # 封装指令信息
        if not chatBotModel.prompt or str(chatBotModel.prompt).isspace():
            prompt = PromptTemplate(
                template=CONVERSATION_CHAT_TEMPLATE,
                input_variables=CONVERSATION_CHAT_VARIABLES
            )
        else:
            prompt = PromptTemplate(
                template=chatBotModel.prompt,
                input_variables=chatBotModel.prompt_variables.split(",")
            )

        adapter = LLMsAdapter(model=chatBotModel.llms, model_name=chatBotModel.get_llm_model_name())
        llm = adapter.get_model_instance(history=ChainModel.init_memory(history=history)[1], question=question)
        return cls.get_instance_with_llm_chain(
            llm=llm,
            prompt_template=prompt,
            verbose=verbose,
            memory=memory,
            history=chat_glm_history,
            question=question,
            **kwargs
        )

    @classmethod
    def get_instance_with_llm_chain_by_history_prompt(
            cls,
            prompt: str,
            prompt_input_variables: List[str],
            memory_history_key: str,
            memory_input_key: str,
            history: List[ChatHistoryModel] = None,
            llm: BaseLanguageModel = None,
            verbose: bool = False,
    ) -> LLMChain:
        """
        获取聊天链实例对象
        :param prompt: 提示词信息
        :param prompt_input_variables: 提示词占位符
        :param memory_history_key:  长程记忆-历史记录占位符字段
        :param memory_input_key: 长程记忆-输入信息占位符字段
        :param history: 历史聊天记录
        :param llm: 大模型对象
        :param verbose: 过程冗余信息
        :return: 聊天链实例对象
        """
        prompt_template = PromptTemplate(template=prompt, input_variables=prompt_input_variables)
        return cls.get_instance_with_llm_chain_by_history(
            prompt_template=prompt_template,
            history=history,
            memory_history_key=memory_history_key,
            memory_input_key=memory_input_key,
            verbose=verbose,
            llm=llm,
        )

    @classmethod
    def get_instance_stream(
            cls,
            question: str,
            chatBotModel: ChatBotModel,
            history: List[ChatHistoryModel] = None,
            model_type: str = MODEL_TYPE_TEXT,
            images: List[str] = [],
            verbose: bool = True,
            **kwargs,
    ) -> RunnableSerializable[dict, str]:
        """
        获取默认的聊天链实例对象
        :param question: 用户问题
        :param chatBotModel: 机器人实体对象
        :param history: 历史聊天记录
        :param verbose: 过程冗余信息
        :param model_type: 模型类型，默认文本模型MODEL_TYPE_TEXT
        :param images: 聊天图片
        :param kwargs: 扩展参数
        :return: 聊天链实例对象
        """
        # 确定用哪个模型
        llms, llm_model_name = cls.get_llms_model(chatBotModel, model_type)

        adapter = LLMsAdapter(model=llms, model_name=llm_model_name)
        llm = adapter.get_model_instance(
            history=ChainModel.init_memory(history=history)[1],
            question=question,
            chatBotModel=chatBotModel,
            model_type=model_type,
            images=images,
            **kwargs
        )
        # 封装指令信息
        prompt = PromptTemplate(
            template=chatBotModel.prompt,
            input_variables=chatBotModel.prompt_variables.split(",")
        )
        parser = StrOutputParser()
        chain = prompt | llm | parser
        return chain

    @classmethod
    def get_llms_model(cls, chatBotModel, model_type=MODEL_TYPE_TEXT):
        llms_models = chatBotModel.llms_models
        llms = chatBotModel.llms if model_type == MODEL_TYPE_TEXT else None
        llm_model_name = chatBotModel.get_llm_model_name() if model_type == MODEL_TYPE_TEXT else None
        if llms_models and model_type in llms_models:
            model = json.loads(llms_models)[model_type]
            llms = model["llms"] if model else None
            llm_model_name = model["modelName"] if model else None
        return llms, llm_model_name

    @classmethod
    def check_llm_model_existing(cls, chatBotModel, model_type=MODEL_TYPE_TEXT):
        llms_models = chatBotModel.llms_models
        if llms_models and model_type in llms_models:
            model = json.loads(llms_models)[model_type]
            return model and model["llms"] and model["modelName"]
        return False

    @classmethod
    def get_instance_with_llm_chain_by_history(
            cls,
            prompt_template: PromptTemplate,
            history: List[ChatHistoryModel] = None,
            memory_history_key: str = MEMORY_HISTORY_KEY,
            memory_input_key: str = MEMORY_INPUT_KEY,
            llm: BaseLanguageModel = None,
            verbose: bool = False,
    ) -> LLMChain:
        """
        获取聊天链实例对象
        :param prompt_template: 提示词模板对象
        :param history: 历史聊天记录
        :param memory_history_key:  长程记忆-历史记录占位符字段
        :param memory_input_key: 长程记忆-输入信息占位符字段
        :param llm: 大模型对象
        :param verbose: 过程冗余信息
        :return: 聊天链实例对象
        """
        # 封装历史聊天记录
        memory, chat_glm_history = cls.init_memory(
            history=history,
            memory_history_key=memory_history_key,
            memory_input_key=memory_input_key
        )
        return cls.get_instance_with_llm_chain(
            prompt_template=prompt_template,
            verbose=verbose,
            memory=memory,
            llm=llm,
        )

    @classmethod
    def get_instance_with_llm_chain(
            cls,
            prompt_template: PromptTemplate,
            verbose: bool = False,
            memory: ConversationBufferMemory = None,
            llm: BaseLanguageModel = None,
            history: List[List[str]] = None,
            **kwargs,
    ) -> LLMChain:
        """
        获取聊天链实例对象
        :param prompt_template: 提示词模板对象
        :param verbose: 过程冗余信息
        :param memory: 长程记忆
        :param llm: 大模型对象
        :param history: 历史聊天记录
        :return: 聊天链实例对象
        """
        llm = llm if llm else LLMsAdapter().get_model_instance(history=history, **kwargs)
        if isinstance(llm, DashScopeAI):
            memory, chat_glm_history = cls.init_memory()
        return LLMChain(
            llm=llm,
            prompt=prompt_template,
            verbose=verbose,
            memory=memory,
        )

    @classmethod
    def get_document_instance(
            cls,
            question: str,
            chatBotModel: ChatBotModel,
            history: List[ChatHistoryModel] = None,
            has_chunk: bool = True,
            **kwargs,
    ) -> BaseCombineDocumentsChain:
        """
        获取文档链
        :param question: 用户问题
        :param chatBotModel: 机器人实体对象
        :param history: 历史聊天记录
        :param has_chunk: 含有分片
        :param kwargs: 扩展参数
        :return: 文档链
        """
        adapter = LLMsAdapter(model=chatBotModel.llms, model_name=chatBotModel.get_llm_model_name())
        llm = adapter.get_model_instance(history=ChainModel.init_memory(history=history)[1], question=question)

        if chatBotModel.is_open_second_prompt() and not has_chunk:
            if chatBotModel.is_refine_chains():
                return ChainModel.get_instance_with_refine(
                    llm=llm,
                    prompt=chatBotModel.suffix_prompt,
                    prefix_prompt=chatBotModel.prefix_prompt,
                    str_prompt_variables=chatBotModel.suffix_prompt_variables,
                    str_prefix_prompt_variables=chatBotModel.prefix_prompt_variables,
                    **kwargs
                )
            else:
                return ChainModel.get_instance_with_stuff(
                    llm=llm,
                    prompt=chatBotModel.suffix_prompt,
                    str_prompt_variables=chatBotModel.suffix_prompt_variables,
                    history=history,
                    **kwargs
                )

        else:
            if chatBotModel.is_refine_chains():
                return ChainModel.get_instance_with_refine(
                    llm=llm,
                    prompt=chatBotModel.prompt,
                    prefix_prompt=chatBotModel.prefix_prompt,
                    str_prompt_variables=chatBotModel.prompt_variables,
                    str_prefix_prompt_variables=chatBotModel.prefix_prompt_variables,
                    **kwargs
                )
            else:
                return ChainModel.get_instance_with_stuff(
                    llm=llm,
                    prompt=chatBotModel.prompt,
                    str_prompt_variables=chatBotModel.prompt_variables,
                    history=history,
                    **kwargs
                )

    @classmethod
    def get_instance_with_refine(
            cls,
            prompt: str,
            prefix_prompt: str,
            prompt_variables: List[str] = None,
            prefix_prompt_variables: List[str] = None,
            llm: BaseLanguageModel = None,
            **kwargs: Any,
    ) -> BaseCombineDocumentsChain:
        """
        Refine模式的文档链
        :param prompt: 提示词信息
        :param prompt_variables: 提示词占位符
        :param prefix_prompt: 提示词前缀信息
        :param prefix_prompt_variables: 提示词前缀占位符
        :param llm: 大模型对象
        :param kwargs: 扩展参数
        :return: 文档链
        """
        llm = LLMsAdapter().get_model_instance(**kwargs) if not llm else llm
        for k, v in kwargs.items():
            if k == "str_prompt_variables":
                prompt_variables = v.split(",")
                continue
            if k == "str_prefix_prompt_variables":
                prefix_prompt_variables = v.split(",")
                continue
        # 校验指令参数信息是否合法
        if not prompt or not prompt_variables or not prefix_prompt or not prefix_prompt_variables:
            logger.error("######ChainModel error[{}], prompt param is not legal.", ERROR_10002)
            raise BusinessException(ERROR_10002.code, ERROR_10002.message)
        # 封装指令模板
        refine_prompt = PromptTemplate(
            input_variables=prompt_variables,
            template=prompt,
        )
        question_prompt = PromptTemplate(
            input_variables=prefix_prompt_variables,
            template=prefix_prompt,
        )
        # 创建链式问答对象
        return load_qa_chain(
            llm=llm,
            chain_type='refine',
            question_prompt=question_prompt,
            refine_prompt=refine_prompt,
            verbose=True,
        )

    @classmethod
    def get_instance_with_stuff(
            cls,
            prompt: str,
            prompt_variables: List[str] = None,
            history: List[ChatHistoryModel] = None,
            llm: BaseLanguageModel = None,
            **kwargs: Any,
    ) -> BaseCombineDocumentsChain:
        """
        Stuff模式的文档链
        :param prompt: 提示词信息
        :param prompt_variables: 提示词占位符
        :param history: 历史聊天记录
        :param llm: 大模型实例对象
        :param kwargs: 扩展参数
        :return: 文档链
        """
        llm = LLMsAdapter().get_model_instance(history=cls.init_memory(history=history)[1],
                                               **kwargs) if not llm else llm
        for k, v in kwargs.items():
            if k == "str_prompt_variables":
                prompt_variables = v.split(",")
                continue
        # 校验指令参数信息是否合法
        if not prompt or not prompt_variables:
            logger.error("######ChainModel error[{}], prompt param is not legal.", ERROR_10002)
            raise BusinessException(ERROR_10002.code, ERROR_10002.message)
        # 封装历史聊天记录
        prompt_template = PromptTemplate(template=prompt, input_variables=prompt_variables)
        if isinstance(llm, DashScopeAI):
            memory = cls.init_memory()[0]
        else:
            memory = cls.init_memory(history=history)[0]
        return load_qa_chain(
            llm=llm,
            chain_type='stuff',
            prompt=prompt_template,
            memory=memory,
            verbose=True,
        )

    @staticmethod
    def init_memory(
            history: List[ChatHistoryModel] = None,
            memory_history_key: str = "chat_history",
            memory_input_key: str = "question"
    ):
        """
        封装历史聊天记录
        :param history: 历史聊天记录
        :param memory_history_key:  长程记忆-历史记录占位符字段
        :param memory_input_key: 长程记忆-输入信息占位符字段
        :return: 长程记忆对象
        """
        memory = ConversationBufferMemory(memory_key=memory_history_key, input_key=memory_input_key)
        if history and len(history) > 0:
            # history转memory倒叙处理
            for h in history[::-1]:
                memory.chat_memory.add_user_message(h.question)
                memory.chat_memory.add_ai_message(h.answer)
        chat_glm_history = [[h.question, h.answer] for h in history[::-1]] if history and len(history) > 0 else []
        return memory, chat_glm_history

    @classmethod
    def get_chat_agent_instance_stream(
            cls,
            chatBotModel: ChatBotModel,
            history: List[ChatHistoryModel] = None,
            model_type: str = MODEL_TYPE_TEXT,
            images: List[str] = [],
            **kwargs,
    ) -> AgentExecutor:
        """
        获取代理执行工具实例对象
        :param chatBotModel: 机器人实体对象
        :param history: 历史聊天记录
        :param model_type: 模型类型，默认文本模型MODEL_TYPE_TEXT
        :param images: 聊天图片
        :param kwargs: 扩展参数
        :return: 聊天链实例对象
        """
        # 确定用哪个模型
        llms, llm_model_name = cls.get_llms_model(chatBotModel, model_type)
        adapter = LLMsAdapter(model=llms, model_name=llm_model_name)
        llm = adapter.get_chat_model_instance(
            history=ChainModel.init_memory(history=history)[1],
            model_type=model_type,
            images=images,
            **kwargs
        )

        prompt_content = chatBotModel.prompt
        if kwargs.get("enable_thinking"):
            prompt_content = THINKING_PROMPT

        if kwargs.get("enable_quick_qa"):
            prompt_content = QUICK_QA_PROMPT

        # 封装指令信息
        system_role = DEFAULT_CHAT_BOT_ROLE
        if chatBotModel and chatBotModel.bot_role:
            system_role = chatBotModel.bot_role
        prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(system_role),
                HumanMessagePromptTemplate.from_template(prompt_content),
                MessagesPlaceholder(variable_name="agent_scratchpad")
            ]
        )
        search = TavilySearchResults(max_results=2, tavily_api_key=TAVILY_API_KEY, name="Tavily")
        tools = [search]
        agent = create_tool_calling_agent(llm, tools, prompt)
        return AgentExecutor(
            max_iterations=3,
            agent=agent,
            tools=tools,
            verbose=False,
            handle_parsing_errors=True
        )

    @classmethod
    def get_chat_instance_stream(
            cls,
            chatBotModel: ChatBotModel,
            history: List[ChatHistoryModel] = None,
            model_type: str = MODEL_TYPE_TEXT,
            images: List[str] = [],
            **kwargs,
    ) -> RunnableSerializable[dict, str]:
        """
        获取聊天模型的聊天链实例对象
        :param chatBotModel: 机器人实体对象
        :param history: 历史聊天记录
        :param model_type: 模型类型，默认文本模型MODEL_TYPE_TEXT
        :param images: 聊天图片
        :param kwargs: 扩展参数
        :return: 聊天链实例对象
        """
        # 确定用哪个模型
        llms, llm_model_name = cls.get_llms_model(chatBotModel, model_type)
        adapter = LLMsAdapter(model=llms, model_name=llm_model_name)
        llm = adapter.get_chat_model_instance(
            history=ChainModel.init_memory(history=history)[1],
            model_type=model_type,
            images=images,
            **kwargs
        )

        prompt_content = chatBotModel.prompt
        if kwargs.get("enable_thinking"):
            prompt_content = THINKING_PROMPT

        if kwargs.get("enable_quick_qa"):
            prompt_content = QUICK_QA_PROMPT

        # 封装指令信息
        system_role = DEFAULT_CHAT_BOT_ROLE
        if chatBotModel and chatBotModel.bot_role:
            system_role = chatBotModel.bot_role
        prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(system_role),
                HumanMessagePromptTemplate.from_template(prompt_content)
            ]
        )
        chain = prompt | llm
        return chain

    @classmethod
    def get_chat_instance_stream_common(
            cls,
            history: List[ChatHistoryModel] = None,
            model: str = None,
            model_name: str = None,
            system_role: str = DEFAULT_CHAT_BOT_ROLE,
            prompt: str = None,
            model_type: str = MODEL_TYPE_TEXT,
            images: List[str] = [],
            **kwargs,
    ) -> RunnableSerializable[dict, str]:
        """
        获取聊天模型的聊天链实例对象
        :param prompt: 提示词
        :param system_role: 角色定义
        :param model: 模型厂商。如：deepseek、dashscop
        :param model_name: 模型名称
        :param history: 历史聊天记录
        :param model_type: 模型类型，默认文本模型MODEL_TYPE_TEXT
        :param images: 聊天图片
        :param kwargs: 扩展参数
        :return: 聊天链实例对象
        """
        # 确定用哪个模型
        adapter = LLMsAdapter(model=model, model_name=model_name)
        llm = adapter.get_chat_model_instance(
            history=ChainModel.init_memory(history=history)[1],
            model_type=model_type,
            images=images,
            **kwargs
        )
        # 封装指令信息
        prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(system_role),
                HumanMessagePromptTemplate.from_template(prompt)
            ]
        )
        chain = prompt | llm
        return chain
