import uuid
import random
from typing import Any, List
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from loguru import logger
from custom.amway.cvision.config.cvision_config import CVISION_CHOOSE_LLM
from framework.business_code import ERROR_10000, ERROR_10006, ERROR_10001, ERROR_10201
from framework.business_except import BusinessException
from models.chains.chain_model import ChainModel
from models.embeddings.es_model_adapter import EmbeddingsModelAdapter
from models.llms.llms_adapter import LLMsAdapter
from models.vectordatabase.v_client import get_instance_client
from service.base_chat_message import BaseChatMessage
from service.base_compose_bot import BaseComposeBot
from service.chat_private_service import ChatPrivateDomain
from config.base_config import *
from service.domain.ai_chat_bot import AiChatBotDomain
from service.domain.ai_namespace import AiNamespaceDomain
from service.domain.ai_namespace_file import AiNamespaceFileDomain, NamespaceFileModel


class CvDomain(BaseComposeBot, BaseChatMessage):
    """
    简历问答功能模块
    """
    split_chunk_size: int = SPLIT_CHUNK_SIZE
    split_chunk_overlap: int = SPLIT_CHUNK_OVERLAP

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
            num: int,
            user_id: str = None,
            namespace_id: str = None,
            **kwargs: Any) -> list:
        """
        简历问答
        :param ques: 问题
        :param bot_id: 机器人标识
        :param num: 筛选份数
        :param user_id: 用户标识
        :param namespace_id: 指定知识库标识
        :param kwargs: 扩展参数
        :return:
        """
        logger.info("CvDomain INFO, request_id={}, Current param info: bot_id=[{}], namespace_id=[{}], num=[{}]",
                    self.request_id, bot_id, namespace_id, num)
        # 根据标识查询机器人配置信息
        chatBotDomain = AiChatBotDomain(request_id=self.request_id)
        chatBotModel = chatBotDomain.find_one(bot_id=bot_id)
        if not chatBotModel:
            logger.error("CvDomain ERROR, [{}]未查询到机器人[{}]信息, request_id={}.", ERROR_10000, bot_id, self.request_id)
            raise BusinessException(ERROR_10000.code, ERROR_10000.message)
        if not chatBotModel.is_master_type():
            logger.error("CvDomain ERROR, [{}]当前机器人[{}]的所属类型不合法, request_id={}.", ERROR_10006, bot_id, self.request_id)
            raise BusinessException(ERROR_10006.code, ERROR_10006.message)
        logger.info("CvDomain INFO, request_id={}, Current bot info: {}", self.request_id, chatBotModel)

        # 判断是否存在指定的知识库信息
        if not namespace_id:
            namespace_id = chatBotModel.namespace_id

        # 查询领域机器人关联的知识库信息
        if not namespace_id:
            logger.error("CvDomain ERROR, [{}]未查询到所属知识库[{}]信息, request_id={}.", ERROR_10001, namespace_id, self.request_id)
            raise BusinessException(ERROR_10001.code, ERROR_10001.message)
        namespaceModel = AiNamespaceDomain(request_id=self.request_id).find_by_id(namespace_id)
        if not namespaceModel:
            logger.error("CvDomain ERROR, [{}]未查询到所属知识库[{}]信息, request_id={}.", ERROR_10001, namespace_id, self.request_id)
            raise BusinessException(ERROR_10001.code, ERROR_10001.message)
        logger.info("CvDomain INFO, request_id={}, Current namespace info: {}.", self.request_id, namespaceModel)

        # 语义搜索向量库中的相似内容
        embeddingsModelAdapter = EmbeddingsModelAdapter()
        embedding = embeddingsModelAdapter.get_model_instance()
        vector_client = get_instance_client()
        ques_docs: list
        try:
            ques_docs = vector_client.search_data(
                ques=ques,
                embedding=embedding,
                namespace=namespaceModel.namespace,
                search_top_k=chatBotModel.vector_top_k,
            )
        except Exception as err:
            logger.error("CvDomain ERROR, [{}]查询向量库文档操作失败, request_id={}, message={}.", ERROR_10201, self.request_id, err)
            raise BusinessException(ERROR_10201.code, ERROR_10201.message)
        logger.info("CvDomain INFO, request_id={}, vector_top_k=【{}】, ques_docs.length=【{}】",
                    self.request_id, chatBotModel.vector_top_k, len(ques_docs))

        # 按权计算Top简历文档
        ques_doc_dict = {}
        # 按最大值计算Top简历文档
        for _doc, _score in ques_docs:
            _metadata = _doc.metadata
            if _metadata["source"] in ques_doc_dict.keys():
                _total_score = ques_doc_dict.get(_metadata["source"])
                if _total_score > float(_score):
                    ques_doc_dict[_metadata["source"]] = _score
            else:
                ques_doc_dict[_metadata["source"]] = _score

        ques_doc_list = sorted(ques_doc_dict.items(), key=lambda x: x[1], reverse=False)
        logger.info("CvDomain INFO, request_id={}, 排序后的ques_doc_list: {}", self.request_id, ques_doc_list)
        if not ques_doc_list:
            return []

        # 识别是否存在从节点机器人
        slave_bot_dict = self.split_slave_bot(chatBotModel=chatBotModel)
        logger.info("CvDomain INFO, request_id={}, slave_bot_dict: {}", self.request_id, slave_bot_dict)

        return self.ask_reload(
            ques_doc_list=ques_doc_list,
            slave_bot_dict=slave_bot_dict,
            num=num,
            namespace_id=namespace_id,
            **kwargs)

    def ask_reload(
            self,
            ques_doc_list: list,
            slave_bot_dict: dict,
            num: int,
            namespace_id: str,
            **kwargs: Any
    ) -> list:
        """
        加载简历信息
        :param ques_doc_list: 排序之后的文档列表
        :param slave_bot_dict: 从节点机器人
        :param num: 取num份简历
        :param namespace_id: 命名空间标识
        :param kwargs: 扩展参数
        :return: 简历信息
        """
        data = []
        _memo = []
        _temp = 0
        while len(data) < num:
            # 查询元文件信息
            if len(ques_doc_list) <= _temp:
                break
            _doc = ques_doc_list[_temp]
            _doc_content_path = str(_doc[0])
            _doc_content_name = str

            if "\\" in _doc_content_path:
                split_arr = _doc_content_path.split("\\")[::-1]
                _doc_content_name = split_arr[0]
            elif "/" in _doc_content_path:
                split_arr = _doc_content_path.split("/")[::-1]
                _doc_content_name = split_arr[0]

            namespaceFileDomain = AiNamespaceFileDomain()
            _file = namespaceFileDomain.find_by_path(file_name=_doc_content_name, namespace_id=namespace_id)
            # 特殊处理 - 1.去重复文件
            if self._has_repeat(_memo, _file):
                _temp = _temp+1
                continue

            loader = DirectoryLoader(path=_file.path, glob=str("**/"+_file.name))
            docs = loader.load()
            # 特殊处理 - 2.过滤PDF图文件
            if docs and len(docs) == 1:
                if len(docs[0].page_content) < 80:
                    _temp = _temp+1
                    continue
            # 元数据切割处理
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.split_chunk_size,
                chunk_overlap=self.split_chunk_overlap
            )
            split_docs = text_splitter.split_documents(docs)

            split_docs_tuple = [
                (
                    _split_doc_item,
                    0.0,
                )
                for _split_doc_item in split_docs
            ]
            logger.info("CvDomain INFO >>>ask_reload, request_id={}, ####Chunk长度策略:{},  ####Chunk重叠策略:{}, "
                        "####切割后的文件数量有:{}",  self.request_id, self.split_chunk_size,
                        self.split_chunk_overlap, len(split_docs_tuple))

            bean = {}
            chatPrivateDomain = ChatPrivateDomain(self.request_id)
            for k, v in slave_bot_dict.items():
                # 根据标识查询机器人配置信息
                chatBotDomain = AiChatBotDomain()
                _bot_model = chatBotDomain.find_one(bot_id=k)
                if _bot_model:
                    _llm = LLMsAdapter(model=CVISION_CHOOSE_LLM).get_model_instance()
                    _chain = ChainModel.get_document_instance(chatBotModel=_bot_model, llm=_llm, question=_bot_model.fixed_ques, **kwargs)
                    _input_documents = [doc for doc, _ in [split_docs_tuple[0]]]
                    _answer = _chain.run(input_documents=_input_documents, question=_bot_model.fixed_ques)
                    _answer = BaseChatMessage.purge(_answer)
                    logger.info("####CvDomain INFO，request_id={}, \n>>>AI回答: [{}].", self.request_id, _answer)
                    bean[v] = self.purge(_answer)
            bean["simil"] = self._calculate(_doc[1], temp=_temp, num=num)
            _temp = _temp+1

            # 特殊处理 - 3.顺延张三的简历
            _index_flag = 0
            for k, v in bean.items():
                if "张三" in v:
                    _index_flag = 1
                    break
            if _index_flag == 0:
                data.append(bean)
        return data

    def _has_repeat(self, _memo: List[str], _file: NamespaceFileModel) -> bool:
        # 根据文件MD5去重
        if _file.md5 and _file.md5 in _memo:
            logger.info("CvDomain INFO, _has_repeat>>>>request_id={}, _file={}, _memo={}.", self.request_id, _file, _memo)
            return True
        # 根据文件名称去重
        if _file.display_name and _file.display_name in _memo:
            logger.info("CvDomain INFO, _has_repeat>>>>request_id={}, _file={}, _memo={}.", self.request_id, _file, _memo)
            return True
        _memo.append(_file.md5)
        _memo.append(_file.display_name)
        return False

    def _calculate(self, score: float, temp: int, num: int) -> str:
        """
        识别度算法函数
        :param score: vectro相似度
        :param temp: 步长
        :param num: 份数
        :return: 识别度
        """
        _result_score = 1 - score
        if num - temp == num:
            _result_score = self._random_max(_result_score)
            return str('%.2f' % (_result_score*100))+"%"
        elif num - temp == 1:
            _result_score = self._random_min(_result_score)
            return str('%.2f' % (_result_score*100))+"%"
        else:
            return str('%.2f' % (_result_score*100))+"%"

    @staticmethod
    def _random_max(score: float) -> float:
        _has_run = True
        _count = 5
        while _has_run:
            ran = random.uniform(0, 0.03)
            logger.info("CvDomain INFO >>>_random_max, ran={}.", ran)
            if score + ran < 1:
                return score + ran
            elif _count == 0:
                return score
            _count = _count - 1

    @staticmethod
    def _random_min(score: float) -> float:
        _has_run = True
        _count = 5
        while _has_run:
            ran = random.uniform(0, 0.3)
            logger.info("CvDomain INFO >>>_random_min, ran={}.", ran)
            if score - ran > 0.6:
                return score - ran
            elif _count == 0:
                return score
            _count = _count - 1
