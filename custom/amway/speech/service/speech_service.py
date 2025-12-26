import uuid
from loguru import logger
from content.prompt_template_chat import (
    CONVERSATION_CHAT_TEMPLATE,
    CONVERSATION_CHAT_VARIABLES,
    MEMORY_HISTORY_KEY,
    MEMORY_INPUT_KEY
)
from custom.amway.speech.config.speech_config import *
from framework.business_except import BusinessException
from models.chains.chain_model import ChainModel
from models.embeddings.es_model_adapter import EmbeddingsModelAdapter
from models.llms.llms_adapter import LLMsAdapter
from models.vectordatabase.v_client import get_instance_client
from service.base_compose_bot import BaseComposeBot
from custom.amway.speech.speech_constant import *
from framework.business_code import (
    ERROR_10000,
    ERROR_10300,
    ERROR_10301,
    ERROR_10202,
    ERROR_10203,
    ERROR_10204,
    ERROR_10205,
)
from service.domain.ai_chat_bot import AiChatBotDomain
from service.domain.ai_namespace import AiNamespaceDomain


class SpeechText(BaseComposeBot):
    """
    演讲稿功能服务
        - 生成演讲稿
    """
    def __init__(
            self,
            ques: str,
            bot_id: str,
            user_id: str = None,
            namespace_id_business: str = None,
            namespace_id_style: str = None,
            request_id: str = str(uuid.uuid4()),
    ):
        """
        构造方法
        :param ques: 问题
        :param bot_id: 机器人标识
        :param user_id: 用户标识
        :param namespace_id_business: 业务背景知识库标识
        :param namespace_id_style: 风格背景知识库标识
        :param request_id: 请求唯一标识
        """
        super().__init__(request_id)
        self.ques = ques
        self.bot_id = bot_id
        self.user_id = user_id
        self.namespace_id_business = namespace_id_business
        self.namespace_id_style = namespace_id_style
        self.request_id = request_id

    def transform(self) -> str:
        """
        生成演讲稿
        :return: 演讲稿
        """
        # 根据标识查询机器人配置信息
        chatBotDomain = AiChatBotDomain()
        chatBotModel = chatBotDomain.find_one(bot_id=self.bot_id)
        if not chatBotModel:
            logger.error("SpeechText ERROR, [{}]未查询到机器人[{}]信息, request_id={}.", ERROR_10000, self.bot_id, self.request_id)
            raise BusinessException(ERROR_10000.code, ERROR_10000.message)
        logger.info("SpeechText INFO, request_id={}, Current bot info: {}", self.request_id, chatBotModel)

        # 查询业务背景知识库信息
        busNamespaceModel = AiNamespaceDomain().find_by_id(self.namespace_id_business)
        if not busNamespaceModel:
            logger.error("SpeechText ERROR, [{}]未查询到指定业务背景知识库[{}]信息, request_id={}.",
                         ERROR_10300, self.namespace_id_business, self.request_id)
            raise BusinessException(ERROR_10300.code, ERROR_10300.message)
        logger.info("SpeechText INFO, request_id={}, Current business namespace info: {}.", self.request_id, busNamespaceModel)
        # 查询风格背景知识库信息
        styleNamespaceModel = AiNamespaceDomain().find_by_id(self.namespace_id_style)
        if not styleNamespaceModel:
            logger.error("SpeechText ERROR, [{}]未查询到指定风格背景知识库[{}]信息, request_id={}.",
                         ERROR_10301, self.namespace_id_style, self.request_id)
            raise BusinessException(ERROR_10301.code, ERROR_10301.message)
        logger.info("SpeechText INFO, request_id={}, Current style namespace info: {}.", self.request_id, styleNamespaceModel)

        # 业务背景知识库中的相关信息
        bus_ques_docs: list
        try:
            bus_ques_docs = get_instance_client().search_data(
                ques=self.ques,
                embedding=EmbeddingsModelAdapter().get_model_instance(),
                namespace=busNamespaceModel.namespace,
                search_top_k=chatBotModel.vector_top_k,
            )
        except Exception as err:
            logger.error("SpeechText ERROR, [{}]查询业务背景的向量库文档操作失败, request_id={}, message={}.", ERROR_10202, self.request_id, err)
            raise BusinessException(ERROR_10202.code, ERROR_10202.message)
        logger.info("SpeechText INFO, search business vector, request_id={}, vector_top_k=【{}】, bus_ques_docs.length=【{}】",
                    self.request_id, chatBotModel.vector_top_k, len(bus_ques_docs))
        if not bus_ques_docs and len(bus_ques_docs) == 0:
            logger.error("SpeechText ERROR, [{}]查询业务背景的向量库文档不能为空, request_id={}.", ERROR_10204, self.request_id)
            raise BusinessException(ERROR_10204.code, ERROR_10204.message)

        # 业务背景知识库中的相关信息
        style_ques_docs: list
        try:
            style_ques_docs = get_instance_client().search_data(
                ques=self.ques,
                embedding=EmbeddingsModelAdapter().get_model_instance(),
                namespace=styleNamespaceModel.namespace,
                search_top_k=chatBotModel.vector_top_k,
            )
        except Exception as err:
            logger.error("SpeechText ERROR, [{}]查询风格背景的向量库文档操作失败, request_id={}, message={}.", ERROR_10203, self.request_id, err)
            raise BusinessException(ERROR_10203.code, ERROR_10203.message)
        logger.info("SpeechText INFO, search style vector, request_id={}, vector_top_k=【{}】, bus_ques_docs.length=【{}】",
                    self.request_id, chatBotModel.vector_top_k, len(style_ques_docs))
        if not style_ques_docs and len(style_ques_docs) == 0:
            logger.error("SpeechText ERROR, [{}]查询风格背景的向量库文档不能为空, request_id={}.", ERROR_10205, self.request_id)
            raise BusinessException(ERROR_10205.code, ERROR_10205.message)

        # 发起问答
        chain_draft = ChainModel.get_instance_with_llm_chain_by_history_prompt(
            prompt=CONVERSATION_CHAT_TEMPLATE,
            prompt_input_variables=CONVERSATION_CHAT_VARIABLES,
            memory_history_key=MEMORY_HISTORY_KEY,
            memory_input_key=MEMORY_INPUT_KEY,
            llm=LLMsAdapter(model=SPEECH_DRAFT_CHOOSE_LLM).get_model_instance(),
        )
        logger.info("SpeechText INFO, >>>>>>>>>>>>1, request_id={}, chain.prompt={}.", self.request_id, chain_draft.prompt)
        answer_draft = chain_draft.predict(question=self.ques)
        logger.info("SpeechText INFO, >>>>>>>>>>>>1, request_id={}, 问题=[{}], 回答结果=[{}].", self.request_id, self.ques, answer_draft)

        speech_prompt = speech_template.replace('{condition}', speech_condition)\
            .replace('{content_business}', bus_ques_docs[0][0].page_content)\
            .replace('{content_style}', style_ques_docs[0][0].page_content)\
            .replace('{content_draft}', answer_draft)

        chain = ChainModel.get_instance_with_llm_chain_by_history_prompt(
            llm=LLMsAdapter(model=SPEECH_RESULT_CHOOSE_LLM).get_model_instance(),
            prompt=speech_prompt,
            prompt_input_variables=speech_variables,
            memory_history_key=speech_history_key,
            memory_input_key=speech_input_key,
        )
        logger.info("SpeechText INFO, >>>>>>>>>>>>2, request_id={}, chain.prompt={}.", self.request_id, chain.prompt)
        answer = chain.predict(question=self.ques)
        logger.info("SpeechText INFO, >>>>>>>>>>>>2, request_id={}, 问题=[{}], 回答结果=[{}].", self.request_id, self.ques, answer)
        return answer
