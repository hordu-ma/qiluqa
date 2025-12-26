import traceback
import uuid
from typing import List

from loguru import logger
from langchain.docstore.document import Document
from langchain_community.document_loaders.directory import DirectoryLoader
from langchain_community.document_loaders.pdf import PyPDFLoader
from framework.business_code import ERROR_10208
from framework.business_except import BusinessException


class CusDocumentLoader:
    """
    文档加载工具
    """
    def __init__(
            self,
            request_id: str = str(uuid.uuid4()),
    ):
        """
        构造函数
        :param request_id: 请求唯一标识
        """
        self.request_id = request_id

    def loader(
            self,
            document_glob: str,
            document_path: str,
    ) -> List[Document]:
        """
        加载文档
        :param document_glob: 文件名称
        :param document_path: 文档目录
        :return: 加载结果
        """
        # 基本参数校验
        if not document_glob or not document_path:
            logger.error("DocumentLoader ERROR, param is not legal, request_id={}, glob={}, doc_content_path={}.",
                         self.request_id, document_glob, document_path)
            raise BusinessException(ERROR_10208.code, ERROR_10208.message)

        if self._is_document_pdf(glob=document_glob):
            file_path = document_path + document_glob
            loader = PyPDFLoader(file_path=file_path)
            return loader.load()
        else:
            file_glob = str("**/" + document_glob)
            loader = DirectoryLoader(path=document_path, glob=file_glob, show_progress=True)
            return loader.load()

    @staticmethod
    def _is_document_pdf(glob: str) -> bool:
        """
        文档是否为PDF类型
        """
        return ".pdf" in glob or ".PDF" in glob

