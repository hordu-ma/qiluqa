import re
import cv2
import uuid
import pytesseract
import threading
from typing import List, Tuple, Dict
from loguru import logger
from langchain_community.document_loaders.directory import DirectoryLoader
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_community.document_loaders import UnstructuredHTMLLoader
from langchain.docstore.document import Document
from config.base_config import *
from service.domain.ai_namespace import NamespaceModel
from service.domain.ai_namespace_file_image import AiNamespaceFileImageDomain
from framework.business_code import ERROR_10208
from framework.business_except import BusinessException
from models.embeddings.es_model_adapter import EmbeddingsModelAdapter
from models.vectordatabase.v_client import get_instance_client
from service.domain.ai_namespace_file import NamespaceFileModel
from service.domain.ai_namespace_file_chunk_strategy import AiChunkStrategyDomain


class LocalRepositoryDomain:
    """
    本地知识库问答模块
    """
    doc_content_path: str = CONTENT_PATH

    def __init__(
            self,
            request_id: str = str(uuid.uuid4()),
    ):
        """
        构造函数
        :param request_id: 请求唯一标识
        """
        self.request_id = request_id
        self.stop_event = threading.Event()

    def push(
            self,
            glob: str,
            namespaceModel: NamespaceModel,
            namespaceFileModel: NamespaceFileModel = None,
    ) -> list[str]:
        """
        向本地知识库推送元数据
        :param glob: 扫描名称
        :param namespaceModel: 所属知识库
        :param namespaceFileModel: 所属知识库文件
        :return: ids
        """
        glob = glob if not namespaceFileModel else namespaceFileModel.name
        doc_content_path = CONTENT_PATH if not namespaceFileModel else namespaceFileModel.path
        docs = self.loader(glob=glob, doc_content_path=doc_content_path)
        logger.info("LocalRepositoryDomain loader INFO, SCENE-4  loading pdf after...")
        logger.info(f"####解析的文档数量有：{len(docs)}")
        logger.info(f"####第一个文档长度有：{len(docs[0].page_content)}")
        # 保险单图片OCR识别文字业务接口
        if namespaceFileModel.display_name == '保险单':
            docs = self.ocr_picture_txt(
                docs=docs
            )
        # 分片规格参数
        namespace = namespaceModel.namespace
        # 以文件定义策略切割分片
        split_docs = AiChunkStrategyDomain(request_id=self.request_id).switch_case_by_chunk_strategy(
            namespaceFileModel=namespaceFileModel,
            docs=docs
        )
        split_docs_new = [
            Document(
                page_content=_doc.page_content,
                metadata=self._get_metadata(
                    document=_doc,
                    namespaceFileModel=namespaceFileModel,
                ),
            )
            for _doc in split_docs
        ]
        # 保存元数据
        embeddingsModelAdapter = EmbeddingsModelAdapter()
        embedding = embeddingsModelAdapter.get_model_instance()
        file_id = str(namespaceFileModel.id) if namespaceFileModel else None
        vector_client = get_instance_client()
        ids = vector_client.insert_data_list(split_docs=split_docs_new, embedding=embedding, namespace=namespace,
                                             file_id=file_id)
        logger.info("####切割后的文件ids有：{}.", ids)
        return ids

    def loader(
            self,
            glob: str,
            doc_content_path: str,
    ) -> List[Document]:
        """
        文件加载
        :param glob: 文件名称
        :param doc_content_path: 目录地址
        :return: 加载结果
        """
        # 基本参数校验
        if not glob or not doc_content_path:
            logger.error("LocalRepositoryDomain loader ERROR, param is not legal, glob={}, doc_content_path={}, "
                         "request_id={}.", glob, doc_content_path, self.request_id)
            raise BusinessException(ERROR_10208.code, ERROR_10208.message)

        if ".pdf" in glob or ".PDF" in glob:
            # loader = PyPDFLoader(file_path=(doc_content_path + glob))
            logger.info("LocalRepositoryDomain loader INFO, SCENE-1  loading pdf before...")
            loader = PyPDFLoader(file_path=(doc_content_path + glob)).load()
            return loader
        if ".html" in glob:
            logger.info("LocalRepositoryDomain loader INFO, SCENE-3  loading html before...")
            loader = UnstructuredHTMLLoader(file_path=(doc_content_path + glob)).load()
            return loader
        else:
            logger.info("LocalRepositoryDomain loader INFO, SCENE-2  loading file before...")
            loader = DirectoryLoader(path=doc_content_path, glob=str("**/" + glob), show_progress=True)
            return loader.load()

    @classmethod
    def _get_metadata(
            cls,
            document: Document,
            namespaceFileModel: NamespaceFileModel = None,
    ) -> Dict:
        page_content = document.page_content
        page_content = page_content.replace("<p>", "")
        page_content = page_content.replace("</p>", "\n")
        metadata = document.metadata
        if namespaceFileModel:
            metadata["name"] = namespaceFileModel.display_name or namespaceFileModel.name
        image_pattern = r'IMAGE\d+'
        image_id_list = re.findall(image_pattern, page_content)
        metadata['images'] = image_id_list
        return metadata

    def search(
            self,
            ques: str,
            namespace_list: list[str] = None,
            vector_search_top_k: int = VECTOR_SEARCH_TOP_K,
    ) -> List[Tuple[Document, float, str]]:
        """
        本地知识库-语义搜索
        :param ques: 问题信息
        :param namespace_list: 向量库标识
        :param vector_search_top_k: 匹配数量
        :return: 向量库文档列表
        """
        embedding = EmbeddingsModelAdapter().get_model_instance()
        vector_client = get_instance_client()
        ques_docs = vector_client.search_data(
            ques=ques,
            embedding=embedding,
            namespace_list=namespace_list,
            search_top_k=vector_search_top_k
        )
        logger.info(
            "####向量库查询结果，request_id={}, \n>>>匹配数: {} \n>>>文档数量: {} \n>>>文档内容: {} \n>>>用户问题: {}",
            self.request_id, vector_search_top_k, len(ques_docs), ques_docs, ques)

        new_ques_docs = [
            (
                _doc,
                _score,
                _file_id,
            )
            for _doc, _score, _file_id in ques_docs if _score == float(0.0)
        ]

        new_ques_docs = new_ques_docs if len(new_ques_docs) > 0 else [
            (
                _doc,
                _score,
                _file_id,
            )
            for _doc, _score, _file_id in ques_docs if _score <= float(VECTOR_SEARCH_SCORE) or _score > 1.0
        ]
        logger.info(
            "####阈值控制筛选结果，request_id={}, \n>>>阈值: {}, \n>>>文档数量: {}, \n>>>文档内容: {} \n>>>用户问题: {}",
            self.request_id, float(VECTOR_SEARCH_SCORE), len(new_ques_docs), new_ques_docs, ques)
        return new_ques_docs

    def ocr_picture_txt(
            self,
            docs: list[Document],
    ):
        image_pattern = r'IMAGE\d+'
        image_id = re.findall(image_pattern, docs[0].page_content)
        namespace_image_domain = AiNamespaceFileImageDomain(self.request_id).find_by_image_id(image_id=image_id[0])
        image_path = namespace_image_domain.path + namespace_image_domain.image_id + namespace_image_domain.type
        logger.info("###ocr_picture_path### image_path={} ", image_path)
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary_img = cv2.threshold(gray, 130, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        custom_config = r'--oem 3 --psm 6'
        new_text = pytesseract.image_to_string(gray, lang='chi_sim+en', config=custom_config)
        logger.info("###ocr_picture_txt### new_txt={} ", new_text)
        docs[0].page_content = new_text
        return docs


"""
    def ocr_picture_txt(
            self,
            docs: list[Document],
    ):
        OCR图像识别算法
        将图片中的文字抽取出来
        try:
            for doc in docs:
                new_text = ''
                image_pattern = r'IMAGE\d+'
                image_id = re.findall(image_pattern, doc.page_content)
                namespace_image_domain = AiNamespaceFileImageDomain(self.request_id).find_by_image_id(
                    image_id=image_id[0])
                image_path = namespace_image_domain.path + namespace_image_domain.image_id + namespace_image_domain.type
                logger.info("###ocr_picture_path### new_txt={} ", image_path)
                reader = easyocr.Reader(['ch_sim'], gpu=True)
                # 10秒为超时
                timeout = 10
                result = self.load_ocr_txt(reader, image_path, timeout)
                for el in result[0]:
                    new_text = new_text + el[1]
                doc.page_content = new_text
            return docs
        except Exception as e:
            logger.error(e)

    def load_ocr_txt(
            self,
            reader,
            image_path: str,
            timeout: int = 10
    ):
        result = []
        try:
            while not self.stop_event.is_set():
                if self.stop_event.wait(timeout=timeout):
                    break
                reader.readtext(image_path, result)
        except Exception as e:
            logger.error(f"OCR processing failed for image: {image_path}, error: {e}")
            raise
        finally:
            self.stop_event.set()
        return result
"""