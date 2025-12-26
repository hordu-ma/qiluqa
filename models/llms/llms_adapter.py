from typing import List, Any

from langchain.base_language import BaseLanguageModel

from config.base_config import *
from config.base_config_chatglm4 import *
from config.base_config_dashscope import BASHSCOPE_MODEL_NAME, BASHSCOPE_BASE_URL, BASHSCOPE_THINKING_URL, \
    BASHSCOPE_VL_URL
from config.base_config_deepseek import DEEPSEEK_MODEL_NAME
from config.base_config_model_type import MODEL_TYPE_TEXT
from config.prod.prod_config_dashscope import PROD_BASHSCOPE_VL_URL
from models.chatai.dashscope.chat_dashscop import ChatDashScopeAI
from models.chatai.deepseek.chat_deepseek import ChatDeepseekAI
from models.llms.baidubce.baidubce import BaidubceAI
from models.llms.chatglm4.chatglm4 import ChatGlm4AI
from models.llms.dashscope.dashscope import DashScopeAI
from models.llms.deepseek.deepseek import DeepseekAI
from models.llms.openai.chatopenai import ChatOpenAI
from service.domain.ai_chat_bot import ChatBotModel


class LLMsAdapter:
    """
    大语言模型 - 适配器
    """

    def __init__(
            self,
            model: str = CURRENT_LLM,
            model_name: str = None,
    ):
        """
        构造函数
        :param model: 大语言模型
        :param model_name: 子模型名称
        """
        self.model = model if model else CURRENT_LLM
        self.model_name = model_name

    def get_model_instance(
            self,
            question: str = None,
            history: List[List[str]] = [],
            chatBotModel: ChatBotModel = None,
            images: List[str] = [],
            model_type: str = MODEL_TYPE_TEXT,
            **kwargs: Any,
    ) -> BaseLanguageModel:
        """
        获取指定的大语言模型实例
        :return: 模型实例
        """
        system_role = DEFAULT_CHAT_BOT_ROLE
        if chatBotModel and chatBotModel.bot_role:
            system_role = chatBotModel.bot_role
        if self.model == "OpenAI":
            model_name = self.model_name if self.model_name else OPENAI_MODEL_NAME
            return ChatOpenAI(history=history, llm_model_name=model_name, system_role=system_role, **kwargs)
        elif self.model == "ChatGlM4":
            model_name = self.model_name if self.model_name else CHATGLM4_MODEL_NAME
            return ChatGlm4AI(
                history=history,
                question=question,
                llm_model_name=model_name,
                temperature=CHATGLM4_TEMPERATURE,
                api_key=CHATGLM4_API_KEY,
                max_tokens=CHATGLM4_MAX_TOKENS,
                url=CHATGLM4_URL,
                top_p=CHATGLM4_TOP_P,
                system_role=system_role
            )
        elif self.model == "Baidubce":
            return BaidubceAI(history=history, system_role=system_role)
        elif self.model == "DashScope":
            model_name = THINKING_MODEL_NAME if kwargs.get("enable_thinking") else self.model_name if self.model_name else BASHSCOPE_MODEL_NAME
            base_url = BASHSCOPE_THINKING_URL if kwargs.get("enable_thinking") else BASHSCOPE_BASE_URL
            return DashScopeAI(base_url=base_url, history=history, llm_model_name=model_name, system_role=system_role,
                               model_type=model_type, images=images, **kwargs)
        elif self.model == "Deepseek":
            model_name = self.model_name if self.model_name else DEEPSEEK_MODEL_NAME
            return DeepseekAI(history=history, llm_model_name=model_name, system_role=system_role, **kwargs)
        else:
            """
            TODO 其他类型的LLMs
            """

    def get_chat_model_instance(
            self,
            history: List[List[str]] = None,
            images: List[str] = [],
            model_type: str = MODEL_TYPE_TEXT,
            **kwargs: Any,
    ) -> BaseLanguageModel:
        """
        获取指定的聊天大语言模型实例
        :return: 模型实例
        """
        if self.model == "DashScope":
            # 当model_type为VL时不考虑enable_thinking
            if model_type == MODEL_TYPE_TEXT:
                model_name = THINKING_MODEL_NAME if kwargs.get("enable_thinking") else self.model_name if self.model_name else BASHSCOPE_MODEL_NAME
                base_url = BASHSCOPE_THINKING_URL if kwargs.get("enable_thinking") else BASHSCOPE_BASE_URL
            else:
                model_name = self.model_name if self.model_name else BASHSCOPE_MODEL_NAME
                base_url = BASHSCOPE_VL_URL
            return ChatDashScopeAI(base_url=base_url, history=history, llm_model_name=model_name,
                                   model_type=model_type, images=images, **kwargs)
        elif self.model == "Deepseek":
            model_name = self.model_name if self.model_name else DEEPSEEK_MODEL_NAME
            return ChatDeepseekAI(history=history, llm_model_name=model_name, **kwargs)
        else:
            """
            TODO 其他类型的LLMs
            """
