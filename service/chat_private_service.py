import json
import uuid
from datetime import datetime
from loguru import logger

from custom.bespin.bespin_sample_service import SampleService
from framework.business_code import ERROR_10007, ERROR_10000, ERROR_10001
from framework.business_except import BusinessException
from models.chains.chain_model import ChainModel
from service.base_chat_message import BaseChatMessage
from service.domain.ai_bot_namespace_relation import AiBotNamespaceRelationDomain
from service.domain.ai_chat_bot import AiChatBotDomain
from service.domain.ai_chat_history import AiChatHistoryDomain
from service.domain.ai_namespace import AiNamespaceDomain
from service.local_repo_service import LocalRepositoryDomain
from service.chat_response import ChatResponse, ChatResponseVO
from typing import Iterator, List, Dict

from service.search_service import SearchService


class ChatPrivateDomain(BaseChatMessage):
    """
    领域知识问答服务
    """

    def __init__(
            self,
            request_id: str = str(uuid.uuid4())
    ):
        """
        构造函数
        :param request_id: 请求唯一标识
        """
        super().__init__(request_id)
        self.request_id = request_id

    def ask(
            self,
            ques: str,
            bot_id: str,
            user_id: str = None,
            group_uuid: str = None,
            is_want_allow_custom: bool = True,
            **kwargs,
    ) -> ChatResponse:
        """
        领域知识问答
        :param ques: 问题
        :param bot_id: 机器人标识
        :param user_id: 用户标识
        :param group_uuid: 会话分组标识
        :param is_want_allow_custom: 是否允许执行定制场景
        :param kwargs: 扩展参数
        :return: AI回答内容
        """
        question_time = datetime.now()
        # 查询机器人信息
        chatBotModel = AiChatBotDomain(request_id=self.request_id).find_one(bot_id=bot_id)
        if not chatBotModel:
            logger.error("ChatPrivateDomain_ask ERROR, [{}]未查询到机器人[{}]信息, request_id={}.", ERROR_10000, bot_id,
                         self.request_id)
            raise BusinessException(ERROR_10000.code, ERROR_10000.message)
        if not chatBotModel.is_private_bot():
            logger.error("ChatPrivateDomain_ask ERROR, [{}]当前机器人[{}]的使用类型不合法, request_id={}.", ERROR_10007,
                         bot_id, self.request_id)
            raise BusinessException(ERROR_10007.code, ERROR_10007.message)
        # 查询知识库信息
        botNamespace_tuple = AiBotNamespaceRelationDomain(request_id=self.request_id).find_nas_id_by_bot_id(
            chatBotModel.bot_id)
        if not botNamespace_tuple:
            logger.error("ChatPrivateDomain_ask ERROR, ask_stream [{}]未查询到所属知识库[{}]信息, request_id={}.",
                         ERROR_10001, chatBotModel.bot_id, self.request_id)
            raise BusinessException(ERROR_10001.code, ERROR_10001.message)
        # 一个机器人关联多个知识库逻辑
        Namespace_list = AiNamespaceDomain(request_id=self.request_id).find_namespace_by_list_id(botNamespace_tuple)
        namespace_list = [str(namespaceModel.namespace) for namespaceModel in Namespace_list]

        # 查询历史聊天记录
        history = self.query_chat_history(
            request_id=self.request_id,
            user_id=user_id,
            bot_id=bot_id,
            memory_limit_size=chatBotModel.memory_limit_size,
            group_uuid=group_uuid
        )
        # 样例插件
        ques, sub_ques = SampleService(request_id=self.request_id).plugin(
            ques=ques,
            chatBotModel=chatBotModel,
            history=ChainModel.init_memory(history=history)[1]
        )

        # 提示词占位符处理
        self.placeholder(
            chatBotModel=chatBotModel,
            request_id=self.request_id,
            **kwargs,
        )

        # 知识库召回逻辑
        ques_docs = LocalRepositoryDomain(request_id=self.request_id).search(
            ques=ques,
            namespace_list=namespace_list,
            vector_search_top_k=chatBotModel.vector_top_k
        )
        # 请求大模型问答功能
        chain = ChainModel.get_document_instance(
            chatBotModel=chatBotModel,
            history=history,
            question=sub_ques,
            has_chunk=len(ques_docs) > 0,
            **kwargs
        )
        metadata, input_documents = self.get_metadata_list(ques_docs=ques_docs)
        answer = chain.run(input_documents=input_documents, question=sub_ques)
        logger.info("####ChatPrivateDomain INFO __1 INFO，request_id={}, \n>>>AI回答: [{}].", self.request_id, answer)
        # 图表标签
        answer = answer + self.get_label_content(metadata=metadata)
        logger.info("####ChatPrivateDomain INFO __2 INFO，request_id={}, \n>>>AI回答: [{}].", self.request_id, answer)
        return self.purge_with_history(
            ques=ques,
            answer=answer,
            metadata=metadata,
            bot_id=bot_id,
            user_id=user_id,
            question_time=question_time,
            chatHistoryDomain=AiChatHistoryDomain(request_id=self.request_id),
            group_uuid=group_uuid,
            **kwargs
        )

    def ask_stream(
            self,
            ques: str,
            bot_id: str,
            user_id: str = None,
            group_uuid: str = None,
            **kwargs,
    ) -> Iterator[ChatResponse]:
        """
        领域知识问答
        :param ques: 问题
        :param bot_id: 机器人标识
        :param user_id: 用户标识
        :param group_uuid: 会话分组标识
        :param kwargs: 扩展参数
        :return: AI回答内容
        """
        question_time = datetime.now()
        # 查询机器人信息
        chatBotModel = AiChatBotDomain(request_id=self.request_id).find_one(bot_id=bot_id)
        if not chatBotModel:
            logger.error("ChatPrivateDomain_ask ERROR, ask_stream [{}]未查询到机器人[{}]信息, request_id={}.",
                         ERROR_10000, bot_id, self.request_id)
            raise BusinessException(ERROR_10000.code, ERROR_10000.message)
        if not chatBotModel.is_private_bot():
            logger.error("ChatPrivateDomain_ask ERROR, ask_stream [{}]当前机器人[{}]的使用类型不合法, request_id={}.",
                         ERROR_10007, bot_id, self.request_id)
            raise BusinessException(ERROR_10007.code, ERROR_10007.message)
        # 查询知识库信息
        botNamespace_tuple = AiBotNamespaceRelationDomain(request_id=self.request_id).find_nas_id_by_bot_id(
            chatBotModel.bot_id)
        if not botNamespace_tuple:
            logger.error("ChatPrivateDomain_ask ERROR, ask_stream [{}]未查询到所属知识库ID[{}]信息, request_id={}.",
                         ERROR_10001, chatBotModel.bot_id, self.request_id)
            raise BusinessException(ERROR_10001.code, ERROR_10001.message)
        # 一个机器人关联多个知识库逻辑
        namespaceModelList = AiNamespaceDomain(request_id=self.request_id).find_namespace_by_list_id(botNamespace_tuple)
        if not namespaceModelList:
            logger.error("ChatPrivateDomain_ask ERROR, ask_stream [{}]未查询到相关知识库[{}]信息, request_id={}.",
                         ERROR_10001, namespaceModelList, self.request_id)
            raise BusinessException(ERROR_10001.code, ERROR_10001.message)
        namespace_list = [str(namespaceModel.namespace) for namespaceModel in namespaceModelList]

        # 查询历史聊天记录
        history = self.query_chat_history(
            request_id=self.request_id,
            user_id=user_id,
            bot_id=bot_id,
            memory_limit_size=chatBotModel.memory_limit_size,
            group_uuid=group_uuid
        )
        # 样例插件
        ques, sub_ques = SampleService(request_id=self.request_id).plugin(
            ques=ques,
            chatBotModel=chatBotModel,
            history=ChainModel.init_memory(history=history)[1]
        )

        # 提示词占位符处理
        self.placeholder(
            chatBotModel=chatBotModel,
            request_id=self.request_id,
            **kwargs,
        )

        # 知识库召回逻辑
        ques_docs = LocalRepositoryDomain(request_id=self.request_id).search(
            ques=ques,
            namespace_list=namespace_list,
            vector_search_top_k=chatBotModel.vector_top_k
        )

        # 请求大模型问答功能
        chain = ChainModel.get_instance_stream(question=sub_ques, chatBotModel=chatBotModel, history=history)
        metadata, input_documents = self.get_metadata_list(ques_docs=ques_docs)
        input_context = [_doc.page_content for _doc in input_documents]
        logger.info("ChatPublicDomain INFO, ask_stream request_id={}, chain.prompt={}.", self.request_id, "?")
        # 增加联网搜索内容
        search: List[Dict] = []
        search_context = []
        if kwargs.get("enable_search"):
            input_results, query_results = SearchService().get_tavily_search_list(ques)
            search = list(query_results)
            search_context.append(input_results)
        answer = ""
        thinking = ""
        is_first = True
        for chunk in chain.stream({"question": sub_ques, "context": input_context, "search_context": search_context,
                                   "chat_history": " "}):
            search_: List[Dict] = []
            if is_first:
                search_ = list(search)
                is_first = False
            chunk = json.loads(chunk) if chunk else chunk
            flag, usage = self.is_dict_with_usage(chunk)
            answer = answer if flag else answer + chunk.get("content")
            answer_ = "[DONE]" if flag else chunk.get("content")
            thinking_ = chunk.get("thinking")
            thinking += thinking_
            if answer_ == "[DONE]":
                # 图表标签
                answer = answer + self.get_label_content(metadata=metadata)
                # 在answer里面增加溯源文件与免责信息
                """
                answer = self.get_answer_has_trace_content(
                    answer,
                    chatBotModel=chatBotModel,
                    namespaceModel=namespaceModel,
                    ques_docs=ques_docs,
                    input_documents=input_documents
                )
                """
                chat_response = self.purge_with_history(
                    ques=ques,
                    answer=answer,
                    metadata=metadata,
                    bot_id=bot_id,
                    user_id=user_id,
                    question_time=question_time,
                    chatHistoryDomain=AiChatHistoryDomain(request_id=self.request_id),
                    group_uuid=group_uuid,
                    llms=chatBotModel.llms,
                    llms_model_name=chatBotModel.get_llm_model_name(),
                    **usage,
                    **kwargs
                )
                chat_response.data.answer = answer_
                chat_response.data.thinking = thinking_
                chat_response.data.search = search_
                yield chat_response
            else:
                yield ChatResponse(
                    data=ChatResponseVO(
                        answer=answer_,
                        thinking=thinking_,
                        search=search_,
                    )
                )
        logger.info(
            "ChatPublicDomain INFO, ask_stream request_id={}, 问题=[{}], 回答结果=[{}],思考过程=[{}],搜索结果=[{}].",
            self.request_id, ques, answer, thinking, search)
