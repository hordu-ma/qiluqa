from abc import ABC, abstractmethod
from typing import (Dict, Any, List, Tuple)
from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from models.vectordatabase.custom.custom_pgvector import EmbeddingStore
from service.namespacefile.namespace_file_metadata import MetadataModel


class BaseVectorClient(ABC):
    """
    向量库客户端
    """
    @abstractmethod
    def delete_data(
            self,
            namespace: str = None,
            ids: list[str] = None,
            delete_all: bool = None,
            **kwargs
    ) -> Dict[str, Any]:
        """
        删除向量数据
        :param namespace: 命名空间标识
        :param ids: 向量标识
        :param delete_all: 是否全部删除
        :param kwargs: 扩展参数
        :return: 未删除成功的ids
        """
        pass

    @abstractmethod
    def delete_file_data(
            self,
            namespace: str = None,
            file_id_list: list[str] = None,
            **kwargs
    ):
        """
        删除向量数据
        :param namespace: 命名空间标识
        :param file_id_list: 文件列表标识
        :param kwargs: 扩展参数
        :return: 未删除成功的ids
        """
        pass

    @abstractmethod
    def query_data(
            self,
            namespace: str = None,
            ids: list[str] = None,
    ) -> List[EmbeddingStore]:
        """
        查询向量数据
        :param namespace: 命名空间标识
        :param ids: 向量标识
        :return: 查询结果
        """
        pass

    @abstractmethod
    def query_page_data(
            self,
            namespace: str = None,
            ids: list[str] = None,
            document: str = None,
            page_nums: int = 0,
            page_size: int = 10,
            file_id: str = None,
            status: str = None
    ):
        """
        查询向量数据
        :param namespace: 命名空间标识
        :param ids:       向量标识
        :param document:  分片信息
        :param page_nums: 分页页码
        :param page_size: 分页条数
        :param file_id:   知识文件标识
        :param status:    分片状态
        :return: 查询结果
        """
        pass

    @abstractmethod
    def update_data(
            self,
            custom_id: str,
            document: str,
            document_text: str,
            namespace: str,
            metadataModel: MetadataModel,
            embedding: Embeddings,
    ):
        """
        查询向量数据
        :param custom_id: 分片标识
        :param document: 分片的明文信息
        :param document_text: 过滤img标签的分片明文信息
        :param namespace: 命名空间标识
        :param metadataModel: 元数据信息
        :param embedding: 稀疏值类型
        """
        pass

    @abstractmethod
    def insert_data(
            self,
            file_id: str,
            document: str,
            document_text: str,
            namespace: str,
            metadataModel: MetadataModel,
            embedding: Embeddings,
    ) -> str:
        """
        新增向量数据
        :param file_id: 文件标识
        :param document: 分片的明文信息
        :param document_text: 过滤图片路径的分片明文信息
        :param namespace: 命名空间标识
        :param metadataModel: 元数据信息
        :param embedding: 稀疏值类型
        """
        pass

    @abstractmethod
    def insert_data_list(
            self,
            split_docs: List[Document],
            embedding: Embeddings,
            namespace: str,
            file_id: str = None,
    ) -> list[str]:
        """
        添加向量数据
        :param split_docs: 分割文件集
        :param embedding: 稀疏值类型
        :param namespace: 命名空间标识
        :param file_id: 知识文件标识
        :return: 向量索引信息
        """
        pass

    @abstractmethod
    def search_data(
            self,
            ques: str,
            embedding: Embeddings,
            namespace_list: list[str],
            search_top_k: int) -> List[Tuple[Document, float, str]]:
        """
        搜索向量数据
        :param ques: 问题
        :param embedding: 稀疏值类型
        :param namespace_list: 命名空间标识
        :param search_top_k: top数
        :return: Chunk文档集合
        """
        pass

    @abstractmethod
    def get_vector_database_type(self) -> str:
        """
        获取向量库的类型名称
        :return: 类型名称
        """
        pass

    @abstractmethod
    def change_vector_status(
            self,
            file_id_list: list[str] = None,
            custom_id_list: list[str] = None,
            status_tag: str = 1
    ):
        """
        改变分片禁用开启状态
        以custom_id_list识别改变的分片
        以tag识别为开启或禁用
        """
        pass
