import re
import uuid
from datetime import datetime
from typing import List, Tuple
from langchain.chains.combine_documents.base import BaseCombineDocumentsChain
from loguru import logger
from langchain.schema import Document
from custom.haleon.haleon_config import (
    CHUNK_IMAGE_LABELS,
    SCRIPT_ANSWER,
    PROBES_ANSWER,
)
from models.chains.chain_model import ChainModel
from service.base_chat_message import BaseChatMessage
from service.base_compose_bot import BaseComposeBot
from service.domain.ai_chat_bot import ChatBotModel
from service.domain.ai_chat_history import ChatHistoryModel
from service.domain.ai_namespace import NamespaceModel
from service.domain.ai_namespace_file_image import AiNamespaceFileImageDomain


class AnswerTypeEnum:
    """
    问答模式枚举类
    """

    def __init__(
            self,
            answer_type: str
    ):
        """
        构造函数
        :param answer_type: 问答类型
        """
        self.answer_type = answer_type

    def is_concise(self) -> bool:
        """
        是否简洁模式
        :return: 识别结果
        """
        return self.answer_type == '0'

    def is_four_stage(self) -> bool:
        """
        是否四段式模式
        :return: 识别结果
        """
        return self.answer_type == '1'

    def is_probe(self) -> bool:
        """
        是否追问模式
        :return: 识别结果
        """
        return self.answer_type == '2'


class HaleonCustomService(BaseChatMessage, BaseComposeBot):
    """
    赫利昂定制服务
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

    def chat_with_haleon(
            self,
            ques: str,
            ques_docs: List[Tuple[Document, float, str]],
            chatBotModel: ChatBotModel,
            namespaceModel: NamespaceModel,
            answer_type: str = '0',
            user_id: str = None,
            group_uuid: str = None,
            history: List[ChatHistoryModel] = None,
            question_time: datetime = datetime.now(),
            **kwargs,
    ):
        """
        赫利昂定制问答功能
        :param ques: 问题
        :param ques_docs: 召回文档
        :param chatBotModel:   机器人实体对象
        :param namespaceModel: 知识库实体对象
        :param answer_type: 回答形式
        :param user_id:     用户标识
        :param group_uuid:  会话分组标识
        :param history:     历史聊天记录
        :param question_time: 发起问答时间
        :param kwargs: 扩展参数
        :return: 问答返回结果
        """
        # 图文合并处理
        label_list = []
        metadata, input_documents = self.get_metadata_list(ques_docs=ques_docs)
        for _doc in input_documents:
            if "images" in _doc.metadata and _doc.metadata["images"]:
                for ims in _doc.metadata["images"]:
                    image_id = ims["image_id"]
                    imageModel = AiNamespaceFileImageDomain(self.request_id).find_by_image_id(image_id)
                    path = str(ims["path"])
                    name = "表" + ims["mark_num"] + " " + imageModel.mark_rsv_f
                    label = str(CHUNK_IMAGE_LABELS).replace("{path}", path).replace("{name}", name)
                    label_list.append(label)

        slave_result = []
        answer_list = []
        enums = AnswerTypeEnum(answer_type=answer_type)
        if enums.is_concise():
            # 简洁模式
            # 在获取namespace_file内溯源名称后，整合到免责声明里面
            answer = self.chat_with_haleon_is_concise(
                ques=ques,
                ques_docs=ques_docs,
                chatBotModel=chatBotModel,
                namespaceModel=namespaceModel,
                history=history,
                **kwargs
            )
        elif enums.is_four_stage():
            # 四段式模式
            answer, slave_result = self.chat_with_haleon_is_four_stage(
                ques=ques,
                ques_docs=ques_docs,
                chatBotModel=chatBotModel,
                namespaceModel=namespaceModel,
                history=history,
                **kwargs
            )
        elif enums.is_probe():
            # 追问模式
            answer, answer_list = self.chat_with_haleon_is_probe(
                ques=ques,
                ques_docs=ques_docs,
                chatBotModel=chatBotModel,
                history=history,
                **kwargs
            )
        else:
            answer = SCRIPT_ANSWER

        # 封装并记录返回结果
        return self.purge_with_history(
            ques=ques,
            answer=answer,
            label_list=label_list,
            bot_id=chatBotModel.bot_id,
            user_id=user_id,
            question_time=question_time,
            group_uuid=group_uuid,
            metadata=metadata,
            slave_result=slave_result,
            answer_list=answer_list,
            **kwargs,
        )

    def chat_with_haleon_is_concise(
            self,
            ques: str,
            ques_docs: List[Tuple[Document, float, str]],
            chatBotModel: ChatBotModel,
            namespaceModel: NamespaceModel,
            history: List[ChatHistoryModel] = None,
            **kwargs,
    ):
        """
        简洁模式
        :param ques: 问题
        :param ques_docs: 召回文档
        :param chatBotModel:   机器人实体对象
        :param namespaceModel: 知识库实体对象
        :param history: 历史聊天记录
        :param kwargs: 扩展参数
        :return: 问答返回结果
        """
        chain = ChainModel.get_document_instance(
            chatBotModel=chatBotModel,
            history=history,
            question=ques,
            has_chunk=len(ques_docs) > 0,
            **kwargs
        )
        input_documents = [doc for doc, _score, _field_id in ques_docs]
        answer = chain.run(input_documents=input_documents, question=ques)
        logger.info("####ChatPrivateDomain chat_with_haleon_is_concise INFO，request_id={}, \n>>>AI回答: [{}].",
                    self.request_id, answer)
        answer = self.get_answer_has_trace_content(
            answer + "\n",
            chatBotModel=chatBotModel,
            namespaceModel=namespaceModel,
            ques_docs=ques_docs,
            input_documents=input_documents
        )
        return answer

    def chat_with_haleon_is_four_stage(
            self,
            ques: str,
            ques_docs: List[Tuple[Document, float, str]],
            chatBotModel: ChatBotModel,
            namespaceModel: NamespaceModel,
            history: List[ChatHistoryModel] = None,
            **kwargs,
    ):
        """
        四段式模式
        :param ques: 问题
        :param ques_docs: 召回文档
        :param chatBotModel: 机器人实体对象
        :param namespaceModel: 知识库实体对象
        :param history: 历史聊天记录
        :param kwargs: 扩展参数
        :return: 问答返回结果
        """
        # 主节点机器人的问题推理
        chain = ChainModel.get_document_instance(
            chatBotModel=chatBotModel,
            history=history,
            question=ques,
            has_chunk=len(ques_docs) > 0,
            **kwargs
        )
        input_documents = [doc for doc, _score, _file_id in ques_docs]
        answer = chain.run(input_documents=input_documents, question=ques)
        logger.info("####ChatPrivateDomain chat_with_haleon_is_four_stage INFO，request_id={}, \n>>>AI回答: [{}].",
                    self.request_id, answer)
        # 调度发起从属机器人的固定问题推理
        slave_result = self.send_ques_by_slave_bot(
            ques=ques,
            chatBotModel=chatBotModel,
            input_documents=input_documents,
            **kwargs
        )
        trace_content_result = ""
        # 在answer中免责和溯源信息
        trace_content_result = self.get_answer_has_trace_content(
            trace_content_result,
            chatBotModel=chatBotModel,
            namespaceModel=namespaceModel,
            ques_docs=ques_docs,
            input_documents=input_documents
        )
        logger.info("####ChatPrivateDomain chat_with_haleon_is_concise INFO，request_id={}, \n>>>AI回答: [{}].",
                    self.request_id, answer)
        slave_result.append(
            {
                "bot_id": "",
                "field": "trace",
                "answer": trace_content_result,
            }
        )
        return answer, slave_result

    def chat_with_haleon_is_probe(
            self,
            ques: str,
            ques_docs: List[Tuple[Document, float, str]],
            chatBotModel: ChatBotModel,
            history: List[ChatHistoryModel] = None,
            **kwargs,
    ):
        """
        追问模式
        :param ques: 问题
        :param ques_docs: 召回文档
        :param chatBotModel: 机器人实体对象
        :param history: 历史聊天记录
        :param kwargs: 扩展参数
        :return: 问答返回结果
        """
        # 发起推理
        chain = ChainModel.get_document_instance(chatBotModel=chatBotModel, history=history, question=ques, **kwargs)
        input_documents = [doc for doc, _, __ in ques_docs]
        answer = ""
        answer_list = []
        retry_num = 5
        while retry_num > 0:
            answer = self._answer_(ques=ques, chain=chain, input_documents=input_documents)
            logger.info("####ChatPrivateDomain chat_with_haleon_is_probe INFO，request_id={}, \n>>>AI回答: [{}].",
                        self.request_id, answer)
            # pattern = "\\d\\.(（){1}.*?\\??(?=（)|\\d\\.\\?|\\d\\..*?(?:？)|\\d\\..*(?=(\\s\\d\\.))"
            pattern = "\\d\\..*?(?=\\d\\.)|\\d\\..*?(?=\\s\\d\\.)|\\d\\..*?$"
            patter_list = re.findall(pattern, answer)
            answer_list = [str(s).split(".")[1].strip() for s in patter_list if s and len(str(s).split(".")) > 1]
            if len(answer_list) == 3:
                retry_num = 0
            else:
                retry_num = retry_num - 1
        probes_list = [PROBES_ANSWER]
        return answer, probes_list + answer_list

    @classmethod
    def _answer_(
            cls,
            ques: str,
            chain: BaseCombineDocumentsChain,
            input_documents: list[Document]
    ):
        return chain.run(input_documents=input_documents, question=ques)


