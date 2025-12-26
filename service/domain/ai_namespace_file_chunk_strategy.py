import uuid
from typing import List
from datetime import datetime
import pymysql
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger
from config.base_config import *
from service.domain.ai_namespace_file import NamespaceFileModel


class ChunkStrategyModel:
    """
    知识库文件实体模型
    """
    def __init__(
            self,
            data: tuple
    ):
        """
        构造函数
        :param data: 数据集合
        """
        self.id = data[0]
        self.deleted = data[1]
        self.creator = data[2]
        self.create_time = data[3]
        self.updator = data[4]
        self.update_time = data[5]
        self.version = data[6]
        self.file_id = data[7]
        self.chunk_strategy = data[8]
        self.chunk_size = data[9]
        self.chunk_overlap = data[10]
        self.chunk_delimiter = data[11]
        self.chunk_delimiter_custom = data[12]
        self.sentence_type = data[13]
        self.window_size = data[14]

    def __str__(self):
        """
        描述函数
        :return: 描述信息
        """
        return "NamespaceFileModel{" \
               "'id': '"+str(self.id)+"', " \
               "'deleted': '"+str(self.deleted)+"', " \
               "'creator': '"+str(self.creator)+"', " \
               "'create_time': '"+str(self.create_time)+"', " \
               "'updator': '"+str(self.updator)+"', " \
               "'update_time': '"+str(self.update_time)+"', " \
               "'version': '"+str(self.version)+"', " \
               "'file_id': '"+str(self.file_id)+"', " \
               "'chunk_strategy': '"+str(self.chunk_strategy)+"', " \
               "'chunk_size': '"+str(self.chunk_size)+"', " \
               "'chunk_overlap': '"+str(self.chunk_overlap)+"', " \
               "'chunk_delimiter': '"+str(self.chunk_delimiter)+"', " \
               "'chunk_delimiter_custom': '"+str(self.chunk_delimiter_custom)+"', " \
               "'sentence_type': '"+str(self.sentence_type)+"', " \
               "'window_size': '"+str(self.window_size)+"'}"


def get_db_conn():
    """
    获取数据库连接对象
    :return: conn数据库连接对象
    """
    return pymysql.connect(
        host=MYSQL_HOST,
        port=int(MYSQL_PORT),
        database=MYSQL_DATABASE,
        charset=MYSQL_CHARSET,
        user=MYSQL_USER,
        passwd=MYSQL_PASSWD
    )


class AiChunkStrategyDomain:
    """
    知识库文件模块
    """
    table_name: str = "ai_namespace_file_chunk_strategy"

    def __init__(
            self,
            request_id: str = str(uuid.uuid4())
    ):
        """
        构造函数
        :param request_id: 请求唯一标识
        """
        self.request_id = request_id

    def is_split_by_context(
            self,
            chunkStrategyModel
    ):
        return str(chunkStrategyModel.sentence_type) == '1'

    def create(
            self,
            namespace_id: str,
            name: str,
            display_name: str,
            path: str,
            type: str,
            size: str,
            vector_ids: list[str],
            remark: str = None,
    ) -> int:
        """
        文件向量化策略表插入数据--还需修改字段
        """
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                path = path.replace("\\", "\\\\")
                vector_ids_str = ','.join(vector_ids)
                current_time = datetime.now()
                sql = f"insert into {self.table_name} " \
                      f"(deleted, " \
                      f"creator, " \
                      f"create_time, " \
                      f"updator, " \
                      f"update_time, " \
                      f"version, " \
                      f"namespace_id, " \
                      f"name, " \
                      f"display_name, " \
                      f"path, " \
                      f"type, " \
                      f"size, " \
                      f"remark, " \
                      f"vector_ids, " \
                      f"vector_status, " \
                      f"vector_count, " \
                      f"channel) " \
                      f"values ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s');" % \
                      ('0', 'system', current_time, 'system', current_time, '0',
                       namespace_id, name, display_name, path, type, size, remark, vector_ids_str, "Done", 0, 'python')

                cursor.execute(sql.encode('utf-8'))
                conn.commit()
                logger.info("Request_id={}, [{}]保存成功!", self.request_id, self.table_name)
                return cursor.lastrowid
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
            return 0
        finally:
            conn.close()

    def update(
            self,
            file_id: int,
            vector_ids: list[str],
            vector_status: str,
            vector_count: int,
            deleted: int = 0,
    ):
        """
        修改文件向量化表数据
        :param file_id: 文件主键标识
        :param vector_ids: 向量标识
        :param vector_status: 向量化状态
        :param vector_count: 向量化重试次数
        :param deleted: 是否删除
        :return: None
        """
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                vector_ids_str = None
                if vector_ids:
                    vector_ids_str = ','.join(vector_ids)
                current_time = datetime.now()
                sql = f"update {self.table_name} set " \
                      f"deleted = '{deleted}', " \
                      f"updator = 'system', " \
                      f"update_time = '{current_time}', " \
                      f"vector_ids = '{vector_ids_str}', " \
                      f"vector_status = '{vector_status}', " \
                      f"vector_count = {vector_count} " \
                      f"where id={file_id}; "
                cursor.execute(sql.encode('utf-8'))
                conn.commit()
                logger.info("Request_id={}, [{}]修改成功!", self.request_id, self.table_name)
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
            return None
        finally:
            conn.close()

    def find_by_condition(
            self,
            file_id: str = None,
    ) -> List[ChunkStrategyModel]:
        """
        查询文件向量化分片策略
        :param file_id: 文件标识
        :return: 分片策略列表
        """
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                sql = f"select id, deleted, creator, create_time, updator, update_time, version, file_id, " \
                      f"chunk_strategy, chunk_size, chunk_overlap, chunk_delimiter, chunk_delimiter_custom, "\
                      f"sentence_type, window_size " \
                      f"from {self.table_name} where deleted = 0 and file_id = '{file_id}'"
                cursor.execute(sql)
                data_list = cursor.fetchall()
                logger.info("Request_id={}, [{}]查询结果：{}, 数据长度：{}.", self.request_id, self.table_name, data_list,
                            len(data_list))
                result_list = []
                for data in data_list:
                    result_list.append(ChunkStrategyModel(data))
                return result_list
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
        finally:
            conn.close()

    def find_by_id(
            self,
            file_id: str,
    ) -> ChunkStrategyModel:
        """
        查询指定的知识库文件
        :param file_id: 文件标识
        :return: 文件列表
        """
        file_list = self.find_by_condition(file_id=file_id)
        return file_list[0] if len(file_list) > 0 else None

    def find_by_status_none(
            self
    ) -> List[ChunkStrategyModel]:
        """
        查询未向量化的文件列表
        :return: 文件列表
        """
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                sql = f"select id, namespace_id, name, path, type, size, remark, vector_ids, " \
                      f"vector_status, vector_count, channel, deleted, creator, create_time, updator, update_time, version, " \
                      f"display_name, trace_name, md5 " \
                      f"from {self.table_name} where vector_status not in ('Wait', 'Done', 'Vectoring') " \
                      f"and vector_count < {SCHEDULES_FILE_RETRY_COUNT} " \
                      f"and deleted = 0 " \
                      f"order by create_time desc " \
                      f"limit {SCHEDULES_FILE_LIMIT_COUNT};"
                cursor.execute(sql)
                data_list = cursor.fetchall()
                logger.info("Request_id={}, [{}]查询结果：{}, 数据长度：{}.", self.request_id, self.table_name, data_list,
                            len(data_list))

                result_list = []
                for data in data_list:
                    result_list.append(ChunkStrategyModel(data))
                return result_list
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
        finally:
            conn.close()

    def case_chunk_strategy(
            self,
            chunk_strategy: str,
            docs: list[Document],
            chunkStrategyModel: ChunkStrategyModel
    ):
        switch_dict = {
            CHUNK_STRATEGY_SMART: self.spilt_chunk_by_customize(docs, chunkStrategyModel),
            CHUNK_STRATEGY_TEXT_LENGTH: self.spilt_chunk_by_customize(docs, chunkStrategyModel),
            CHUNK_STRATEGY_TEXT_SENTENCE: self.spilt_chunk_by_customize(docs, chunkStrategyModel,
                                                                        separators=SEPARATORS_SENTENCE),
        }
        return switch_dict.get(chunk_strategy)

    def switch_case_by_chunk_strategy(
            self,
            namespaceFileModel: NamespaceFileModel,
            docs: list[Document]
    ):
        """
        对文件分片策略进行分类处理
        不同的分片策略使用不同的方法
        """
        if not namespaceFileModel or namespaceFileModel.type.lower() == 'html':
            split_docs = self.spilt_chunk_by_customize(docs)
        else:
            chunkStrategyModel = self.find_by_id(namespaceFileModel.id)
            chunk_strategy = chunkStrategyModel.chunk_strategy
            if (chunkStrategyModel.chunk_strategy == CHUNK_STRATEGY_TEXT_SENTENCE and
                    self.is_split_by_context(chunkStrategyModel=chunkStrategyModel)):
                chunkStrategyModel.chunk_strategy = CHUNK_STRATEGY_TEXT_SENTENCE_BY_WINDOW
            split_docs = self.case_chunk_strategy(
                chunk_strategy=chunk_strategy,
                docs=docs,
                chunkStrategyModel=chunkStrategyModel
            )
        return split_docs

    def spilt_chunk_by_customize(
            self,
            docs:  list[Document],
            chunkStrategyModel: ChunkStrategyModel = None,
            separators: list[str] = None
    ):
        """
        智能切割分片策略
        自定义切割文本-字符长度分片
        """
        # 定义切割符
        if chunkStrategyModel:
            split_chunk_size = chunkStrategyModel.chunk_size or SPLIT_CHUNK_SIZE
            split_chunk_overlap = chunkStrategyModel.chunk_overlap or SPLIT_CHUNK_OVERLAP
            if chunkStrategyModel.chunk_delimiter:
                if chunkStrategyModel.chunk_delimiter_custom:
                    separators = chunkStrategyModel.chunk_delimiter.split(',')+chunkStrategyModel.chunk_delimiter_custom.split(',')
                else:
                    separators = chunkStrategyModel.chunk_delimiter.split(',')
            if chunkStrategyModel.chunk_delimiter_custom:
                separators = chunkStrategyModel.chunk_delimiter_custom.split(',')
        else:
            split_chunk_size = SPLIT_CHUNK_SIZE
            split_chunk_overlap = SPLIT_CHUNK_OVERLAP
        if split_chunk_size == -1:
            total_length = 0
            for _doc in docs:
                total_length = total_length + len(_doc.page_content)
            split_chunk_size = total_length/split_chunk_overlap
        split_docs = RecursiveCharacterTextSplitter(
            chunk_size=split_chunk_size,
            chunk_overlap=split_chunk_overlap,
            separators=separators,
            is_separator_regex=True
        ).split_documents(docs)
        logger.info("####Chunk长度策略：{}, request_id={}.", split_chunk_size, self.request_id)
        logger.info("####Chunk重叠策略：{}, request_id={}.", split_chunk_overlap, self.request_id)
        logger.info("####切割后的文件数量有：{}, request_id={}.", len(split_docs), self.request_id)
        return split_docs
