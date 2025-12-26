import uuid
from typing import List, Tuple, Dict, Any

from langchain.embeddings.base import Embeddings
from langchain.schema import Document
from models.vectordatabase.custom.custom_pgvector import PGVector, DistanceStrategy, EmbeddingStore

from config.base_config import *
from models.embeddings.es_model_adapter import EmbeddingsModelAdapter
from models.vectordatabase.base_vector_client import BaseVectorClient
from service.namespacefile.namespace_file_metadata import MetadataModel


class VectorPostgresClient(BaseVectorClient):
    """
    Postgres向量库客户端
    """
    pgvector_driver: str = PGVECTOR_DRIVER
    pgvector_host: str = PGVECTOR_HOST
    pgvector_port: str = PGVECTOR_PORT
    pgvector_database: str = PGVECTOR_DATABASE
    pgvector_user: str = PGVECTOR_USER
    pgvector_password: str = PGVECTOR_PASSWORD

    def __get_db_conn(self):
        CONNECTION_STRING = PGVector.connection_string_from_db_params(
            driver=self.pgvector_driver,
            host=self.pgvector_host,
            port=int(self.pgvector_port),
            database=self.pgvector_database,
            user=self.pgvector_user,
            password=self.pgvector_password
        )
        return CONNECTION_STRING

    def delete_data(
            self,
            namespace: str = None,
            ids: list[str] = None,
            delete_all: bool = None,
            **kwargs
    ):
        embeddingsModelAdapter = EmbeddingsModelAdapter()
        embedding = embeddingsModelAdapter.get_model_instance()

        if delete_all:
            PGVector.from_existing_index(
                embedding=embedding,
                collection_name=namespace,
                connection_string=self.__get_db_conn(),
                distance_strategy=DistanceStrategy.COSINE,
                pre_delete_collection=False
            ).delete_collection()
        else:
            PGVector.from_existing_index(
                embedding=embedding,
                collection_name=namespace,
                connection_string=self.__get_db_conn(),
                distance_strategy=DistanceStrategy.COSINE,
                pre_delete_collection=False
            ).delete_embeddings(ids=ids)

    def delete_file_data(
            self,
            namespace: str = None,
            file_id_list: list[str] = None,
            **kwargs
    ):
        embeddingsModelAdapter = EmbeddingsModelAdapter()
        embedding = embeddingsModelAdapter.get_model_instance()
        return PGVector.from_existing_index(
            embedding=embedding,
            collection_name=namespace,
            connection_string=self.__get_db_conn(),
            distance_strategy=DistanceStrategy.COSINE,
            pre_delete_collection=False
        ).delete_file_embeddings(file_id_list=file_id_list)

    def query_data(
            self,
            namespace: str = None,
            ids: list[str] = None
    ) -> List[EmbeddingStore]:
        return PGVector.from_existing_index(
                embedding=EmbeddingsModelAdapter().get_model_instance(),
                collection_name=namespace,
                connection_string=self.__get_db_conn(),
                distance_strategy=DistanceStrategy.COSINE,
                pre_delete_collection=False
        ).query_embeddings(ids=ids)

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
        return PGVector.from_existing_index(
            embedding=EmbeddingsModelAdapter().get_model_instance(),
            collection_name=namespace,
            connection_string=self.__get_db_conn(),
            distance_strategy=DistanceStrategy.COSINE,
            pre_delete_collection=False,
        ).pages_embeddings(ids=ids, document=document, namespace=namespace, page_nums=page_nums, page_size=page_size,
                           file_id=file_id, status=status)

    def insert_data(
            self,
            file_id: str,
            document: str,
            document_text: str,
            namespace: str,
            metadataModel: MetadataModel,
            embedding: Embeddings,
    ) -> str:
        custom_id = str(uuid.uuid4()).replace("-", "")
        PGVector.from_existing_index(
                embedding=embedding,
                collection_name=namespace,
                connection_string=self.__get_db_conn(),
                distance_strategy=DistanceStrategy.COSINE,
                pre_delete_collection=False,
        ).insert_embeddings(custom_id=custom_id, file_id=file_id, document=document,
                            document_text=document_text, metadataModel=metadataModel)
        return custom_id

    def insert_data_list(
            self,
            split_docs: List[Document],
            embedding: Embeddings,
            namespace: str,
            file_id: str = None,
    ) -> list[str]:
        ids = [str(uuid.uuid4()).replace("-", "") for n in range(0, len(split_docs))]
        PGVector.from_documents(
            documents=split_docs,
            embedding=embedding,
            collection_name=namespace,
            connection_string=self.__get_db_conn(),
            distance_strategy=DistanceStrategy.COSINE,
            pre_delete_collection=False,
            ids=ids,
            file_id=file_id,
        )
        return ids

    def search_data(
            self,
            ques: str,
            embedding: Embeddings,
            namespace_list: list[str],
            search_top_k: int
    ) -> List[Tuple[Document, float, str]]:
        store = PGVector.from_existing_collection_list(
            embedding=embedding,
            collection_name_list=namespace_list,
            connection_string=self.__get_db_conn(),
            distance_strategy=DistanceStrategy.COSINE,
            pre_delete_collection=False
        )
        return store.similarity_search_with_score(query=ques, k=search_top_k)

    def update_data(
            self,
            custom_id: str,
            document: str,
            document_text: str,
            namespace: str,
            metadataModel: MetadataModel,
            embedding: Embeddings,
    ):
        store = PGVector.from_existing_index(
            embedding=embedding,
            collection_name=namespace,
            connection_string=self.__get_db_conn(),
            distance_strategy=DistanceStrategy.COSINE,
            pre_delete_collection=False
        )
        store.update_embeddings(custom_id=custom_id, document=document,
                                document_text=document_text, metadataModel=metadataModel)

    def change_vector_status(
            self,
            file_id_list: list[str] = None,
            custom_id_list: list[str] = None,
            status_tag: str = 1
    ):
        PGVector.from_existing_index(
            embedding=EmbeddingsModelAdapter().get_model_instance(),
            connection_string=self.__get_db_conn(),
            distance_strategy=DistanceStrategy.COSINE,
            pre_delete_collection=False
        ).change_status(file_id_list=file_id_list, custom_id_list=custom_id_list, status_tag=status_tag)

    def get_vector_database_type(self) -> str:
        return 'Postgres'
