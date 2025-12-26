import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from loguru import logger
from langchain_community.document_loaders import DirectoryLoader
from langchain.schema import Document
from config.base_config import SPLIT_CHUNK_SIZE, SPLIT_CHUNK_OVERLAP
from custom.amway.amway_config import SFT_SOURCE_PATH, SFT_TARGET_PATH
from models.chains.chain_model import ChainModel
from custom.amway.sft.config.sft_config import *
from custom.amway.sft.sft_constant import *
from models.llms.llms_adapter import LLMsAdapter


class SftDataService:
    """
    SFT微调自生成数据服务
    """
    def __init__(
            self,
            source_file_path: str,
            target_file_path: str,
    ):
        """
        构造函数
        :param source_file_path: 需要微调的源文件目录
        :param target_file_path: 指定微调数据的存放目录
        """
        self.source_file_path = source_file_path
        self.target_file_path = target_file_path
        logger.info("#########Init SftDataService, source_file_path={}, target_file_path={}",
                    source_file_path, target_file_path)

    def reload(
            self,
            glob: str = "**/*.txt"
    ) -> List[Document]:
        """
        加载指定目录下的文件集
        :param glob: 文件格式
        :return: 文件集
        """
        loader = DirectoryLoader(path=self.source_file_path, glob=glob)
        docs = loader.load()
        logger.info(f"####解析的文档数量有：{len(docs)}")
        return docs

    def _create(
            self,
            doc: Document,
            data: list
    ):
        """
        创建
        :param doc: 文档对象
        :param data: SFT数据
        :return: None
        """
        file_name = split_file_metadata(metadata=doc.metadata)
        file_path = self.target_file_path + file_name
        with open(file_path, "w") as file:
            file.write(json.dumps(data, ensure_ascii=False))

    @staticmethod
    def _get_abstract(
            doc: Document,
            request_id: str = str(uuid.uuid4())
    ) -> str:
        """
        生成摘要信息
        :param doc: 文档对象
        :param request_id: 请求唯一标识
        :return: 摘要信息
        """
        split_docs = RecursiveCharacterTextSplitter(
            chunk_size=SPLIT_CHUNK_SIZE,
            chunk_overlap=SPLIT_CHUNK_OVERLAP
        ).split_documents([doc])
        chain = ChainModel.get_instance_with_refine(
            prompt=prompt_template_abstract,
            prompt_variables=prompt_template_abstract_variables,
            prefix_prompt=prefix_prompt_template_abstract,
            prefix_prompt_variables=prefix_prompt_template_abstract_variables,
            llm=LLMsAdapter(model=SFT_SPEECH_ABSTRACT_CHOOSE_LLM).get_model_instance(),
        )
        logger.info("SftDataService abstract INFO, request_id={}, 指令=[{}].", request_id, chain)
        answer = chain.run(input_documents=split_docs, question="帮我生成这份文本的摘要")
        logger.info("SftDataService abstract INFO, request_id={}, 摘要=[{}].", request_id, answer)
        return split_answer(answer=answer)

    def _get_outlines(
            self,
            doc: Document,
            temp: int = 0,
            request_id: str = str(uuid.uuid4())
    ) -> List[str]:
        """
        生成大纲信息
        :param doc: 文档对象
        :param request_id: 请求唯一标识
        :return: 大纲信息
        """
        split_docs = RecursiveCharacterTextSplitter(
            chunk_size=SPLIT_CHUNK_SIZE,
            chunk_overlap=SPLIT_CHUNK_OVERLAP
        ).split_documents([doc])
        chain = ChainModel.get_instance_with_refine(
            prompt=prompt_template_outline,
            prompt_variables=prompt_template_outline_variables,
            prefix_prompt=prefix_prompt_template_outline,
            prefix_prompt_variables=prefix_prompt_template_outline_variables,
            llm=LLMsAdapter(model=SFT_SPEECH_OUTLINES_CHOOSE_LLM).get_model_instance(),
        )
        logger.info("SftDataService outlines INFO, request_id={}, 指令=[{}].", request_id, chain)
        answer = chain.run(input_documents=split_docs, question="帮我生成这份文本的大纲")
        logger.info("SftDataService outlines INFO, request_id={}, 大纲=[{}].", request_id, answer)
        s_answer = split_answer(answer=answer)
        o_answer = split_outline(answer=s_answer)
        if len(o_answer) == 0 and temp < 3:
            temp = temp + 1
            return self._get_outlines(doc=doc, temp=temp, request_id=request_id)
        return o_answer

    @staticmethod
    def _get_paragraph(
            doc: Document,
            outline: str,
            request_id: str = str(uuid.uuid4()),
    ) -> str:
        """
        生成段落信息
        :param doc: 文档对象
        :param outline: 大纲段落
        :param request_id: 请求唯一标识
        :return: 段落信息
        """
        split_docs = RecursiveCharacterTextSplitter(
            chunk_size=SPLIT_CHUNK_SIZE,
            chunk_overlap=SPLIT_CHUNK_OVERLAP
        ).split_documents([doc])
        chain = ChainModel.get_instance_with_refine(
            prompt=prompt_template_paragraph,
            prompt_variables=prompt_template_paragraph_variables,
            prefix_prompt=prefix_prompt_template_paragraph,
            prefix_prompt_variables=prefix_prompt_template_paragraph_variables,
            llm=LLMsAdapter(model=SFT_SPEECH_PARAGRAPH_CHOOSE_LLM).get_model_instance(),
        )
        logger.info("SftDataService paragraph INFO, request_id={}, 指令=[{}].", request_id, chain)
        answer = chain.run(input_documents=split_docs, question=outline)
        logger.info("SftDataService paragraph INFO, request_id={}, 大纲=[{}] 段落=[{}].", request_id, outline, answer)
        return split_answer(answer=answer)

    @staticmethod
    def _init_sft_data(
            abstract: str,
            outline: str,
            paragraph: str,
    ) -> object:
        """
        初始化生成SFT数据
        :param abstract: 摘要
        :param outline: 大纲
        :param paragraph: 段落
        :return: SFT数据
        """
        data = {
            "instruction": "你是一个演讲稿生成专家，给定演讲稿摘要：" + abstract + "。其某段的标题大纲是：" + outline + "请生成对应的演讲稿的大纲内容：",
            "input": "",
            "output": paragraph,
        }
        return data

    def transform(
            self,
            request_id: str = str(uuid.uuid4())
    ):
        """
        转换SFT数据
        :param request_id: 请求唯一标识
        :return: None
        """
        docs = self.reload()
        for doc in docs:
            try:
                _result_list = []
                abstract = self._get_abstract(doc=doc, request_id=request_id)
                outlines = self._get_outlines(doc=doc, request_id=request_id)
                for outline in outlines:
                    paragraph = self._get_paragraph(doc=doc, outline=outline, request_id=request_id)
                    _result = self._init_sft_data(abstract=abstract, outline=outline, paragraph=paragraph)
                    _result_list.append(_result)
                logger.info(f"######Transform after, _result_list内容长度：{len(_result_list)}")
                if len(_result_list) > 0:
                    self._create(doc=doc, data=_result_list)
            except Exception as err:
                logger.error("####SftDataService ERROR, request_id={}, message={}", request_id, err)
                continue


if __name__ == "__main__":
    service = SftDataService(
        source_file_path=SFT_SOURCE_PATH,
        target_file_path=SFT_TARGET_PATH,
    )
    service.transform()
