from __future__ import annotations

from datetime import datetime

from loguru import logger
import enum
import logging
import uuid
import sqlalchemy
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Session, declarative_base, relationship
from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from langchain.utils import get_from_dict_or_env
from langchain.vectorstores.base import VectorStore
from config.base_config import PGVECTOR_DIMENSIONS
from service.namespacefile.namespace_file_metadata import MetadataModel

Base = declarative_base()  # type: Any


ADA_TOKEN_COUNT = int(PGVECTOR_DIMENSIONS)
_LANGCHAIN_DEFAULT_COLLECTION_NAME = "langchain"


class BaseModel(Base):
    __abstract__ = True
    uuid = sqlalchemy.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class CollectionStore(BaseModel):
    __tablename__ = "langchain_pg_collection"

    name = sqlalchemy.Column(sqlalchemy.String)
    cmetadata = sqlalchemy.Column(JSON)

    embeddings = relationship(
        "EmbeddingStore",
        back_populates="collection",
        passive_deletes=True,
    )

    @classmethod
    def get_by_name(cls, session: Session, name: str) -> Optional["CollectionStore"]:
        return session.query(cls).filter(cls.name == name).first()  # type: ignore

    @classmethod
    def get_by_name_list(cls, session: Session, name_list: list[str]):
        return session.query(cls).filter(cls.name.in_(name_list)).all() #查询所有相关知识库信息

    @classmethod
    def get_or_create(
        cls,
        session: Session,
        name: str,
        cmetadata: Optional[dict] = None,
    ) -> Tuple["CollectionStore", bool]:
        """
        Get or create a collection.
        Returns [Collection, bool] where the bool is True if the collection was created.
        """
        created = False
        collection = cls.get_by_name(session, name)
        if collection:
            return collection, created

        collection = cls(name=name, cmetadata=cmetadata)
        session.add(collection)
        session.commit()
        created = True
        return collection, created


class EmbeddingStore(BaseModel):
    __tablename__ = "langchain_pg_embedding"

    collection_id = sqlalchemy.Column(
        UUID(as_uuid=True),
        sqlalchemy.ForeignKey(
            f"{CollectionStore.__tablename__}.uuid",
            ondelete="CASCADE",
        ),
    )
    collection = relationship(CollectionStore, back_populates="embeddings")
    embedding: Vector = sqlalchemy.Column(Vector(ADA_TOKEN_COUNT))
    document = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    cmetadata = sqlalchemy.Column(JSON, nullable=True)
    custom_id = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    file_id = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    create_date = sqlalchemy.Column(sqlalchemy.TIMESTAMP, nullable=True)
    update_date = sqlalchemy.Column(sqlalchemy.TIMESTAMP, nullable=True)
    status = sqlalchemy.Column(sqlalchemy.String, default='1', nullable=True)
    number = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    @classmethod
    def delete_by_file_id(cls, session: Session, file_id_list: list[str]) -> Optional[int]:
        query = session.query(cls).filter(cls.file_id.in_(file_id_list))
        return query.delete()

    @classmethod
    def get_by_custom_id(cls, session: Session, custom_id: str) -> Optional["EmbeddingStore"]:
        return session.query(cls).filter(cls.custom_id == custom_id).first()  # type: ignore

    @classmethod
    def delete_by_custom_id_list(cls, session: Session, custom_id_list: list[str]):
        query = session.query(cls).filter(cls.custom_id.in_(custom_id_list))
        return query.delete()

    @classmethod
    def get_list_by_custom_id(cls, session: Session, ids: List[str]) -> Optional[List["EmbeddingStore"]]:
        return session.query(cls).filter(cls.custom_id.in_(ids)).all()

    @classmethod
    def update_status_by_custom_list(
            cls,
            session: Session,
            custom_id_list: list[str] = None,
            file_id_list: list[str] = None,
            status_tag: str = 1
    ):
        # 更新分片禁用启用状态
        if file_id_list:
            return (session.query(cls).filter(cls.file_id.in_(file_id_list)).
                    update({cls.status: status_tag}))
        if custom_id_list:
            return (session.query(cls).filter(cls.custom_id.in_(custom_id_list)).
                update({cls.status: status_tag}))

    @classmethod
    def get_number_by_file_id(cls, session: Session, file_id: str) -> int:
        # 获取相关fild_id文件的分片序号
        results = session.query(cls.number).filter(cls.file_id == file_id).all()
        numbers = [int(result[0]) for result in results]
        return max(numbers) if numbers else 0

    @classmethod
    def get_page_data(
            cls,
            session: Session,
            ids: List[str],
            document: str,
            page_nums: int,
            page_size: int,
            collection_id: str,
            file_id: str,
    ) -> Optional[List["CollectionStore"]]:
        limits = page_size
        offset = (page_nums - 1) * page_size
        if not document:
            if not ids:
                if not file_id:
                    return session.query(cls).filter(cls.collection_id == collection_id).order_by(sqlalchemy.asc("create_date"))[offset:offset + limits]
                else:
                    return session.query(cls).filter(cls.collection_id == collection_id, cls.file_id == file_id).order_by(sqlalchemy.asc("create_date"))[offset:offset + limits]
            else:
                if not file_id:
                    return session.query(cls).filter(cls.collection_id == collection_id, cls.custom_id.in_(ids)).order_by(sqlalchemy.asc("create_date"))[offset:offset + limits]
                else:
                    return session.query(cls).filter(cls.collection_id == collection_id, cls.custom_id.in_(ids), cls.file_id == file_id).order_by(sqlalchemy.asc("create_date"))[offset:offset + limits]
        else:
            if not ids:
                if not file_id:
                    return session.query(cls).filter(cls.collection_id == collection_id, cls.document.like('%'+document+'%')).order_by(sqlalchemy.asc("create_date"))[offset:offset + limits]
                else:
                    return session.query(cls).filter(cls.collection_id == collection_id, cls.document.like('%'+document+'%'), cls.file_id == file_id).order_by(sqlalchemy.asc("create_date"))[offset:offset + limits]
            else:
                if not file_id:
                    return session.query(cls).filter(cls.collection_id == collection_id, cls.document.like('%'+document+'%'), cls.custom_id.in_(ids)).order_by(sqlalchemy.asc("create_date"))[offset:offset + limits]
                else:
                    return session.query(cls).filter(cls.collection_id == collection_id, cls.document.like('%'+document+'%'), cls.custom_id.in_(ids), cls.file_id == file_id).order_by(sqlalchemy.asc("create_date"))[offset:offset + limits]

    @classmethod
    def get_page_data_by_status(
            cls,
            session: Session,
            ids: List[str],
            document: str,
            page_nums: int,
            page_size: int,
            collection_id: str,
            file_id: str,
            status: str
    ) -> Optional[List["CollectionStore"]]:
        limits = page_size
        offset = (page_nums - 1) * page_size
        if not document:
            if not ids:
                if not file_id:
                    return session.query(cls).filter(cls.collection_id == collection_id, cls.status == status).order_by(
                        sqlalchemy.asc("create_date"))[offset:offset + limits]
                else:
                    return session.query(cls).filter(cls.collection_id == collection_id,
                                                     cls.file_id == file_id, cls.status == status).order_by(sqlalchemy.asc("create_date"))[
                           offset:offset + limits]
            else:
                if not file_id:
                    return session.query(cls).filter(cls.collection_id == collection_id,
                                                     cls.custom_id.in_(ids), cls.status == status).order_by(sqlalchemy.asc("create_date"))[
                           offset:offset + limits]
                else:
                    return session.query(cls).filter(cls.collection_id == collection_id, cls.custom_id.in_(ids),
                                                     cls.file_id == file_id, cls.status == status).order_by(sqlalchemy.asc("create_date"))[
                           offset:offset + limits]
        else:
            if not ids:
                if not file_id:
                    return session.query(cls).filter(cls.collection_id == collection_id,
                                                     cls.document.like('%' + document + '%'), cls.status == status).order_by(
                        sqlalchemy.asc("create_date"))[offset:offset + limits]
                else:
                    return session.query(cls).filter(cls.collection_id == collection_id,
                                                     cls.document.like('%' + document + '%'),
                                                     cls.file_id == file_id, cls.status == status).order_by(sqlalchemy.asc("create_date"))[
                           offset:offset + limits]
            else:
                if not file_id:
                    return session.query(cls).filter(cls.collection_id == collection_id,
                                                     cls.document.like('%' + document + '%'),
                                                     cls.custom_id.in_(ids), cls.status == status).order_by(sqlalchemy.asc("create_date"))[
                           offset:offset + limits]
                else:
                    return session.query(cls).filter(cls.collection_id == collection_id,
                                                     cls.document.like('%' + document + '%'), cls.custom_id.in_(ids),
                                                     cls.file_id == file_id, cls.status == status).order_by(sqlalchemy.asc("create_date"))[
                           offset:offset + limits]

    @classmethod
    def get_page_count(
            cls,
            session: Session,
            ids: List[str],
            document: str,
            collection_id: str,
            file_id: str,
    ) -> int:
        if not document:
            if not ids:
                if not file_id:
                    return session.query(cls).filter(cls.collection_id == collection_id).count()
                else:
                    return session.query(cls).filter(cls.collection_id == collection_id, cls.file_id == file_id).count()
            else:
                if not file_id:
                    return session.query(cls).filter(cls.collection_id == collection_id, cls.custom_id.in_(ids)).count()
                else:
                    return session.query(cls).filter(cls.collection_id == collection_id, cls.custom_id.in_(ids), cls.file_id == file_id).count()
        else:
            if not ids:
                if not file_id:
                    return session.query(cls).filter(cls.collection_id == collection_id, cls.document.like('%'+document+'%')).count()
                else:
                    return session.query(cls).filter(cls.collection_id == collection_id, cls.document.like('%'+document+'%'), cls.file_id == file_id).count()
            else:
                if not file_id:
                    return session.query(cls).filter(cls.collection_id == collection_id, cls.document.like('%'+document+'%'), cls.custom_id.in_(ids)).count()
                else:
                    return session.query(cls).filter(cls.collection_id == collection_id, cls.document.like('%'+document+'%'), cls.custom_id.in_(ids), cls.file_id == file_id).count()

    @classmethod
    def get_page_count_by_status(
            cls,
            session: Session,
            ids: List[str],
            document: str,
            page_nums: int,
            page_size: int,
            collection_id: str,
            file_id: str,
            status: str
    ) -> Optional[List["CollectionStore"]]:
        if not document:
            if not ids:
                if not file_id:
                    return session.query(cls).filter(cls.collection_id == collection_id, cls.status == status).count()
                else:
                    return session.query(cls).filter(cls.collection_id == collection_id,
                                                     cls.file_id == file_id, cls.status == status).count()
            else:
                if not file_id:
                    return session.query(cls).filter(cls.collection_id == collection_id,
                                                     cls.custom_id.in_(ids), cls.status == status).count()
                else:
                    return session.query(cls).filter(cls.collection_id == collection_id, cls.custom_id.in_(ids),
                                                     cls.file_id == file_id, cls.status == status).count()
        else:
            if not ids:
                if not file_id:
                    return session.query(cls).filter(cls.collection_id == collection_id,
                                                     cls.document.like('%' + document + '%'), cls.status == status).count()
                else:
                    return session.query(cls).filter(cls.collection_id == collection_id,
                                                     cls.document.like('%' + document + '%'),
                                                     cls.file_id == file_id, cls.status == status).count()
            else:
                if not file_id:
                    return session.query(cls).filter(cls.collection_id == collection_id,
                                                     cls.document.like('%' + document + '%'),
                                                     cls.custom_id.in_(ids), cls.status == status).count()
                else:
                    return session.query(cls).filter(cls.collection_id == collection_id,
                                                     cls.document.like('%' + document + '%'), cls.custom_id.in_(ids),
                                                     cls.file_id == file_id, cls.status == status).count()


class QueryResult:
    EmbeddingStore: EmbeddingStore
    distance: float


class DistanceStrategy(str, enum.Enum):
    EUCLIDEAN = EmbeddingStore.embedding.l2_distance
    COSINE = EmbeddingStore.embedding.cosine_distance
    MAX_INNER_PRODUCT = EmbeddingStore.embedding.max_inner_product


class PGVector(VectorStore):
    """
    VectorStore implementation using Postgres and pgvector.
    - `connection_string` is a postgres connection string.
    - `embedding_function` any embedding function implementing
        `langchain.embeddings.base.Embeddings` interface.
    - `collection_name` is the name of the collection to use. (default: langchain)
        - NOTE: This is not the name of the table, but the name of the collection.
            The tables will be created when initializing the store (if not exists)
            So, make sure the user has the right permissions to create tables.
    - `distance_strategy` is the distance strategy to use. (default: EUCLIDEAN)
        - `EUCLIDEAN` is the euclidean distance.
        - `COSINE` is the cosine distance.
    - `pre_delete_collection` if True, will delete the collection if it exists.
        (default: False)
        - Useful for testing.
    """

    def __init__(
        self,
        connection_string: str,
        embedding_function: Embeddings,
        collection_name: str = _LANGCHAIN_DEFAULT_COLLECTION_NAME,
        collection_name_list: list[str] = None,
        collection_metadata: Optional[dict] = None,
        distance_strategy: DistanceStrategy = DistanceStrategy.COSINE,
        pre_delete_collection: bool = False,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.connection_string = connection_string
        self.embedding_function = embedding_function
        self.collection_name = collection_name
        self.collection_name_list = collection_name_list
        self.collection_metadata = collection_metadata
        self.distance_strategy = distance_strategy
        self.pre_delete_collection = pre_delete_collection
        self.logger = logger or logging.getLogger(__name__)
        self.__post_init__()

    def __post_init__(
        self,
    ) -> None:
        """
        Initialize the store.
        """
        self._conn = self.connect()
        # self.create_vector_extension()
        self.create_tables_if_not_exists()
        self.create_collection()

    def connect(self) -> sqlalchemy.engine.Connection:
        engine = sqlalchemy.create_engine(self.connection_string)
        conn = engine.connect()
        return conn

    def create_vector_extension(self) -> None:
        try:
            with Session(self._conn) as session:
                statement = sqlalchemy.text("CREATE EXTENSION IF NOT EXISTS vector")
                session.execute(statement)
                session.commit()
        except Exception as e:
            self.logger.exception(e)

    def create_tables_if_not_exists(self) -> None:
        with self._conn.begin():
            Base.metadata.create_all(self._conn)

    def drop_tables(self) -> None:
        with self._conn.begin():
            Base.metadata.drop_all(self._conn)

    def create_collection(self) -> None:
        if self.pre_delete_collection:
            self.delete_collection()
        with Session(self._conn) as session:
            CollectionStore.get_or_create(
                session, self.collection_name, cmetadata=self.collection_metadata
            )

    def delete_collection(self) -> None:
        self.logger.debug("Trying to delete collection")
        with Session(self._conn) as session:
            collection = self.get_collection(session)
            if not collection:
                self.logger.warning("Collection not found")
                return
            session.delete(collection)
            session.commit()

    def get_collection(self, session: Session) -> Optional["CollectionStore"]:
        return CollectionStore.get_by_name(session, self.collection_name)

    def get_collection_list(self, session: Session) -> List[CollectionStore.uuid]:
        collection_ids = []
        collectionStore = CollectionStore.get_by_name_list(session, self.collection_name_list)
        for collection in collectionStore:
            collection_ids.append(collection.uuid)
        return collection_ids

    @classmethod
    def __from(
        cls,
        texts: List[str],
        embeddings: List[List[float]],
        embedding: Embeddings,
        metadatas: Optional[List[dict]] = None,
        ids: Optional[List[str]] = None,
        collection_name: str = _LANGCHAIN_DEFAULT_COLLECTION_NAME,
        distance_strategy: DistanceStrategy = DistanceStrategy.COSINE,
        pre_delete_collection: bool = False,
        **kwargs: Any,
    ) -> PGVector:
        if ids is None:
            ids = [str(uuid.uuid1()) for _ in texts]

        if not metadatas:
            metadatas = [{} for _ in texts]

        connection_string = cls.get_connection_string(kwargs)

        store = cls(
            connection_string=connection_string,
            collection_name=collection_name,
            embedding_function=embedding,
            distance_strategy=distance_strategy,
            pre_delete_collection=pre_delete_collection,
        )

        store.add_embeddings(
            texts=texts, embeddings=embeddings, metadatas=metadatas, ids=ids, **kwargs
        )

        return store

    def delete_embeddings(
            self,
            ids: List[str],
    ) -> None:
        with Session(self._conn) as session:
            EmbeddingStore.delete_by_custom_id_list(session=session, custom_id_list=ids)
            session.commit()

    def delete_file_embeddings(
            self,
            file_id_list: list[str],
    ):
        with Session(self._conn) as session:
            EmbeddingStore.delete_by_file_id(session=session, file_id_list=file_id_list)
            session.commit()

    def query_embeddings(
            self,
            ids: List[str],
    ) -> List[EmbeddingStore]:
        with Session(self._conn) as session:
            return EmbeddingStore.get_list_by_custom_id(
                session=session,
                ids=ids
            )

    def pages_embeddings(
            self,
            ids: List[str],
            document: str,
            namespace: str,
            page_nums: int,
            page_size: int,
            file_id: str,
            status: str = None
    ):
        with Session(self._conn) as session:
            _collection = CollectionStore.get_by_name(session=session, name=namespace)
            if not status:
                data_list = EmbeddingStore.get_page_data(
                    session=session,
                    ids=ids,
                    document=document,
                    page_nums=page_nums,
                    page_size=page_size,
                    collection_id=str(_collection.uuid),
                    file_id=file_id,
                )
                data_count = EmbeddingStore.get_page_count(
                    session=session,
                    ids=ids,
                    document=document,
                    collection_id=str(_collection.uuid),
                    file_id=file_id,
                )
            else:
                data_list = EmbeddingStore.get_page_data_by_status(
                    session=session,
                    ids=ids,
                    document=document,
                    page_nums=page_nums,
                    page_size=page_size,
                    collection_id=str(_collection.uuid),
                    file_id=file_id,
                    status=status
                )
                data_count = EmbeddingStore.get_page_count_by_status(
                    session=session,
                    ids=ids,
                    document=document,
                    page_nums=page_nums,
                    page_size=page_size,
                    collection_id=str(_collection.uuid),
                    file_id=file_id,
                    status=status
                )
            return data_list, data_count

    def update_embeddings(
            self,
            custom_id: str,
            document: str,
            document_text: str,
            metadataModel: MetadataModel
    ):
        with Session(self._conn) as session:
            embeddingStore = EmbeddingStore.get_by_custom_id(session=session, custom_id=custom_id)
            if not embeddingStore:
                return
            # 明文信息
            if document and document != embeddingStore.document:
                embedding = self.embedding_function.embed_query(text=document_text)
                embeddingStore.embedding = embedding
                embeddingStore.document = document
                embeddingStore.status = 1
            embeddingStore.update_date = datetime.now()
            embeddingStore.cmetadata = metadataModel.default_serializer()
            session.commit()

    def change_status(
            self,
            file_id_list: list[str] = None,
            custom_id_list: list[str] = None,
            status_tag: str = 1
    ):
        """
        对分片禁用开启状态进行修改
        依分片uuid和tag为依据进行开启禁用
        """
        with Session(self._conn) as session:
            embeddingStore = EmbeddingStore.update_status_by_custom_list(
                session=session,
                custom_id_list=custom_id_list,
                file_id_list=file_id_list,
                status_tag=status_tag
            )
            logger.info("######change_vector_status_count INFO, embeddingStore_len={}", embeddingStore)
            session.commit()

    def insert_embeddings(
            self,
            custom_id: str,
            file_id: str,
            document: str,
            document_text: str,
            metadataModel: MetadataModel
    ):
        with Session(self._conn) as session:
            collection = self.get_collection(session)
            embedding = self.embedding_function.embed_query(text=document_text)
            # 获取分片序号
            number = EmbeddingStore.get_number_by_file_id(file_id=file_id, session=session)+1
            embedding_store = EmbeddingStore(
                embedding=embedding,
                document=document,
                cmetadata=metadataModel.default_serializer(),
                custom_id=custom_id,
                file_id=file_id,
                create_date=datetime.now(),
                update_date=datetime.now(),
                number=str(number)
            )
            collection.embeddings.append(embedding_store)
            session.add(embedding_store)
            logger.info("######insert Chunk INFO, Chunk custom_id={}", custom_id)
            session.commit()

    def add_embeddings(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[dict],
        ids: List[str],
        **kwargs: Any,
    ) -> None:
        # 设置每个文件的分片序号
        number = 1
        # 知识库文件标识
        file_id = None
        for k, v in kwargs.items():
            if k == "file_id":
                file_id = v if v else None
                break
        logger.info("######PGvector INFO, get session before... mark={}", ids[0])
        with Session(self._conn) as session:
            logger.info("######PGvector INFO, get session after... mark={}", ids[0])
            collection = self.get_collection(session)
            logger.info("######PGvector INFO, get collection after... mark={}", ids[0])
            if not collection:
                logger.info("######PGvector INFO, get collection is empty... mark={}", ids[0])
                raise ValueError("Collection not found")
            for text, metadata, embedding, id in zip(texts, metadatas, embeddings, ids):
                embedding_store = EmbeddingStore(
                    embedding=embedding,
                    document=text,
                    cmetadata=metadata,
                    custom_id=id,
                    file_id=file_id,
                    create_date=datetime.now(),
                    update_date=datetime.now(),
                    number=number,
                    status='1'
                )
                number = number+1
                collection.embeddings.append(embedding_store)
                session.add(embedding_store)
            logger.info("######PGvector INFO,  ... mark={}.", ids[0])
            session.commit()
            logger.info("######PGvector INFO, commit step 2... mark={}.", ids[0])

    def add_texts(
        self,
        texts: Iterable[str],
        metadatas: Optional[List[dict]] = None,
        ids: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> List[str]:
        """Run more texts through the embeddings and add to the vectorstore.

        Args:
            texts: Iterable of strings to add to the vectorstore.
            metadatas: Optional list of metadatas associated with the texts.
            kwargs: vectorstore specific parameters

        Returns:
            List of ids from adding the texts into the vectorstore.
        """
        if ids is None:
            ids = [str(uuid.uuid1()) for _ in texts]

        embeddings = self.embedding_function.embed_documents(list(texts))

        if not metadatas:
            metadatas = [{} for _ in texts]

        with Session(self._conn) as session:
            collection = self.get_collection(session)
            if not collection:
                raise ValueError("Collection not found")
            for text, metadata, embedding, id in zip(texts, metadatas, embeddings, ids):
                embedding_store = EmbeddingStore(
                    embedding=embedding,
                    document=text,
                    cmetadata=metadata,
                    custom_id=id,
                )
                collection.embeddings.append(embedding_store)
                session.add(embedding_store)
            session.commit()

        return ids

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[dict] = None,
        **kwargs: Any,
    ) -> List[Document]:
        """Run similarity search with PGVector with distance.

        Args:
            query (str): Query text to search for.
            k (int): Number of results to return. Defaults to 4.
            filter (Optional[Dict[str, str]]): Filter by metadata. Defaults to None.

        Returns:
            List of Documents most similar to the query.
        """
        embedding = self.embedding_function.embed_query(text=query)
        return self.similarity_search_by_vector(
            embedding=embedding,
            k=k,
            filter=filter,
        )

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter: Optional[dict] = None,
    ) -> List[Tuple[Document, float, str]]:
        """Return docs most similar to query.

        Args:
            query: Text to look up documents similar to.
            k: Number of Documents to return. Defaults to 4.
            filter (Optional[Dict[str, str]]): Filter by metadata. Defaults to None.

        Returns:
            List of Documents most similar to the query and score for each
        """
        embedding = self.embedding_function.embed_query(query)
        docs = self.similarity_search_with_score_by_vector(
            embedding=embedding, k=k, filter=filter
        )
        return docs

    def similarity_search_with_score_by_vector(
        self,
        embedding: List[float],
        k: int = 4,
        filter: Optional[dict] = None,
    ) -> List[Tuple[Document, float, str]]:
        with Session(self._conn) as session:
            collection_ids = self.get_collection_list(session)
            if not collection_ids:
                raise ValueError("collection_ids not found")

            filter_by = EmbeddingStore.collection_id.in_(collection_ids)

            if filter is not None:
                filter_clauses = []
                for key, value in filter.items():
                    IN = "in"
                    if isinstance(value, dict) and IN in map(str.lower, value):
                        value_case_insensitive = {
                            k.lower(): v for k, v in value.items()
                        }
                        filter_by_metadata = EmbeddingStore.cmetadata[key].astext.in_(
                            value_case_insensitive[IN]
                        )
                        filter_clauses.append(filter_by_metadata)
                    else:
                        filter_by_metadata = EmbeddingStore.cmetadata[
                            key
                        ].astext == str(value)
                        filter_clauses.append(filter_by_metadata)

                filter_by = sqlalchemy.and_(filter_by, *filter_clauses)

            results: List[QueryResult] = (
                session.query(
                    EmbeddingStore,
                    self.distance_strategy(embedding).label("distance"),  # type: ignore
                )
                .filter(filter_by)
                .filter(EmbeddingStore.status == '1')
                .order_by(sqlalchemy.asc("distance"))
                .join(
                    CollectionStore,
                    EmbeddingStore.collection_id == CollectionStore.uuid,
                )
                .limit(k)
                .all()
            )

        docs = [
            (
                Document(
                    page_content=result.EmbeddingStore.document,
                    metadata=result.EmbeddingStore.cmetadata,
                ),
                result.distance if self.embedding_function is not None else None,
                result.EmbeddingStore.file_id if result.EmbeddingStore.file_id else "",
            )
            for result in results
        ]
        return docs

    def similarity_search_by_vector(
        self,
        embedding: List[float],
        k: int = 4,
        filter: Optional[dict] = None,
        **kwargs: Any,
    ) -> List[Document]:
        """Return docs most similar to embedding vector.

        Args:
            embedding: Embedding to look up documents similar to.
            k: Number of Documents to return. Defaults to 4.
            filter (Optional[Dict[str, str]]): Filter by metadata. Defaults to None.

        Returns:
            List of Documents most similar to the query vector.
        """
        docs_and_scores = self.similarity_search_with_score_by_vector(
            embedding=embedding, k=k, filter=filter
        )
        return [doc for doc, _ in docs_and_scores]

    @classmethod
    def from_texts(
        cls: Type[PGVector],
        texts: List[str],
        embedding: Embeddings,
        metadatas: Optional[List[dict]] = None,
        collection_name: str = _LANGCHAIN_DEFAULT_COLLECTION_NAME,
        distance_strategy: DistanceStrategy = DistanceStrategy.COSINE,
        ids: Optional[List[str]] = None,
        pre_delete_collection: bool = False,
        **kwargs: Any,
    ) -> PGVector:
        """
        Return VectorStore initialized from texts and embeddings.
        Postgres connection string is required
        "Either pass it as a parameter
        or set the PGVECTOR_CONNECTION_STRING environment variable.
        """
        new_texts = [t.encode("utf-8").decode("utf-8", errors="replace").replace("\x00", "\uFFFD") for t in texts]
        embeddings = embedding.embed_documents(list(new_texts))
        logger.info("################from_texts>>>  new_texts.length={},  embeddings.length={}.",
                    len(new_texts), len(embeddings))
        return cls.__from(
            new_texts,
            embeddings,
            embedding,
            metadatas=metadatas,
            ids=ids,
            collection_name=collection_name,
            distance_strategy=distance_strategy,
            pre_delete_collection=pre_delete_collection,
            **kwargs,
        )

    @classmethod
    def from_embeddings(
        cls,
        text_embeddings: List[Tuple[str, List[float]]],
        embedding: Embeddings,
        metadatas: Optional[List[dict]] = None,
        collection_name: str = _LANGCHAIN_DEFAULT_COLLECTION_NAME,
        distance_strategy: DistanceStrategy = DistanceStrategy.COSINE,
        ids: Optional[List[str]] = None,
        pre_delete_collection: bool = False,
        **kwargs: Any,
    ) -> PGVector:
        """Construct PGVector wrapper from raw documents and pre-
        generated embeddings.

        Return VectorStore initialized from documents and embeddings.
        Postgres connection string is required
        "Either pass it as a parameter
        or set the PGVECTOR_CONNECTION_STRING environment variable.

        Example:
            .. code-block:: python

                from langchain import PGVector
                from langchain.embeddings import OpenAIEmbeddings
                embeddings = OpenAIEmbeddings()
                text_embeddings = embeddings.embed_documents(texts)
                text_embedding_pairs = list(zip(texts, text_embeddings))
                faiss = PGVector.from_embeddings(text_embedding_pairs, embeddings)
        """
        texts = [t[0] for t in text_embeddings]
        embeddings = [t[1] for t in text_embeddings]

        return cls.__from(
            texts,
            embeddings,
            embedding,
            metadatas=metadatas,
            ids=ids,
            collection_name=collection_name,
            distance_strategy=distance_strategy,
            pre_delete_collection=pre_delete_collection,
            **kwargs,
        )

    @classmethod
    def from_existing_index(
        cls: Type[PGVector],
        embedding: Embeddings,
        collection_name: str = _LANGCHAIN_DEFAULT_COLLECTION_NAME,
        distance_strategy: DistanceStrategy = DistanceStrategy.COSINE,
        pre_delete_collection: bool = False,
        **kwargs: Any,
    ) -> PGVector:
        """
        Get instance of an existing PGVector store.This method will
        return the instance of the store without inserting any new
        embeddings
        """

        connection_string = cls.get_connection_string(kwargs)

        store = cls(
            connection_string=connection_string,
            collection_name=collection_name,
            embedding_function=embedding,
            distance_strategy=distance_strategy,
            pre_delete_collection=pre_delete_collection,
        )

        return store

    @classmethod
    def from_existing_collection_list(
            cls: Type[PGVector],
            embedding: Embeddings,
            collection_name_list: List[str] = None,
            distance_strategy: DistanceStrategy = DistanceStrategy.COSINE,
            pre_delete_collection: bool = False,
            **kwargs: Any,
    ) -> PGVector:
        """
        Get instance of an existing PGVector store.This method will
        return the instance of the store without inserting any new
        embeddings
        """

        connection_string = cls.get_connection_string(kwargs)

        store = cls(
            connection_string=connection_string,
            collection_name_list=collection_name_list,
            embedding_function=embedding,
            distance_strategy=distance_strategy,
            pre_delete_collection=pre_delete_collection,
        )

        return store

    @classmethod
    def get_connection_string(cls, kwargs: Dict[str, Any]) -> str:
        connection_string: str = get_from_dict_or_env(
            data=kwargs,
            key="connection_string",
            env_key="PGVECTOR_CONNECTION_STRING",
        )

        if not connection_string:
            raise ValueError(
                "Postgres connection string is required"
                "Either pass it as a parameter"
                "or set the PGVECTOR_CONNECTION_STRING environment variable."
            )

        return connection_string

    @classmethod
    def from_documents(
        cls: Type[PGVector],
        documents: List[Document],
        embedding: Embeddings,
        collection_name: str = _LANGCHAIN_DEFAULT_COLLECTION_NAME,
        distance_strategy: DistanceStrategy = DistanceStrategy.COSINE,
        ids: Optional[List[str]] = None,
        pre_delete_collection: bool = False,
        **kwargs: Any,
    ) -> PGVector:
        """
        Return VectorStore initialized from documents and embeddings.
        Postgres connection string is required
        "Either pass it as a parameter
        or set the PGVECTOR_CONNECTION_STRING environment variable.
        """
        texts = [d.page_content for d in documents]
        metadatas = [d.metadata for d in documents]
        connection_string = cls.get_connection_string(kwargs)

        kwargs["connection_string"] = connection_string

        return cls.from_texts(
            texts=texts,
            pre_delete_collection=pre_delete_collection,
            embedding=embedding,
            distance_strategy=distance_strategy,
            metadatas=metadatas,
            ids=ids,
            collection_name=collection_name,
            **kwargs,
        )

    @classmethod
    def connection_string_from_db_params(
        cls,
        driver: str,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
    ) -> str:
        """Return connection string from database parameters."""
        return f"postgresql+{driver}://{user}:{password}@{host}:{port}/{database}"
