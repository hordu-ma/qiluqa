import uuid
from typing import List
from datetime import datetime
import pymysql
from loguru import logger
from config.base_config import MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, MYSQL_CHARSET, MYSQL_USER, MYSQL_PASSWD, \
    SCHEDULES_FILE_RETRY_COUNT, SCHEDULES_FILE_LIMIT_COUNT


class NamespaceFileModel:
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
        self.namespace_id = data[1]
        self.name = data[2]
        self.path = data[3]
        self.type = data[4]
        self.size = data[5]
        self.remark = data[6]
        self.vector_ids = data[7]
        self.vector_status = data[8]
        self.vector_count = data[9]
        self.channel = data[10]
        self.deleted = data[11]
        self.creator = data[12]
        self.create_time = data[13]
        self.updator = data[14]
        self.update_time = data[15]
        self.version = data[16]
        self.display_name = data[17]
        self.trace_name = data[18]
        self.md5 = data[19]

    def __str__(self):
        """
        描述函数
        :return: 描述信息
        """
        return "NamespaceFileModel{" \
               "'id': '"+str(self.id)+"', " \
               "'namespace_id': '"+str(self.namespace_id)+"', " \
               "'name': '"+str(self.name)+"', " \
               "'path': '"+str(self.path)+"', " \
               "'type': '"+str(self.type)+"', " \
               "'size': '"+str(self.size)+"', " \
               "'remark': '"+str(self.remark)+"', " \
               "'vector_ids': '"+str(self.vector_ids)+"', " \
               "'vector_status': '"+str(self.vector_status)+"', " \
               "'vector_count': '"+str(self.vector_count)+"', " \
               "'channel': '"+str(self.channel)+"', " \
               "'deleted': '"+str(self.deleted)+"', " \
               "'creator': '"+str(self.creator)+"', " \
               "'create_time': '"+str(self.create_time)+"', " \
               "'updator': '"+str(self.updator)+"', " \
               "'update_time': '"+str(self.update_time)+"', " \
               "'version': '"+str(self.version)+"', " \
               "'display_name': '"+str(self.display_name)+"', " \
               "'trace_name': '" + str(self.trace_name) + "', " \
               "'md5': '"+str(self.md5) + "'}"

    def is_want_generate_chunk(self) -> bool:
        """
        知识文件是否可以生成分片
        :return: 识别结果
        """
        return self.vector_status in ('None', 'Wait', 'Fail')


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


class AiNamespaceFileDomain:
    """
    知识库文件模块
    """
    table_name: str = "ai_namespace_file"

    def __init__(
            self,
            request_id: str = str(uuid.uuid4())
    ):
        """
        构造函数
        :param request_id: 请求唯一标识
        """
        self.request_id = request_id

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
        创建知识库文件信息
        :param namespace_id: 知识库标识
        :param name: 文件名称
        :param display_name: 文件显示名称
        :param path: 文件路径
        :param type: 文件类型
        :param size: 文件大小
        :param remark: 备注信息
        :param vector_ids: 向量标识
        :return: 自增长序号
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

    def insert(
            self,
            namespace_id: str,
            file_id: str,
            creator: str,
            trace_name: str,
            name: str,
            display_name: str,
            path: str,
            type: str,
            size: int,
            remark: str = None,

    ) -> int:
        """
        插入知识库文件信息
        :param namespace_id: 知识库标识
        :param name: 文件名称
        :param display_name: 文件显示名称
        :param path: 文件路径
        :param type: 文件类型
        :param size: 文件大小
        :param remark: 备注信息
        :param file_id: 文件标识
        :param creator: 文件创建者
        :param trace_name: 溯源文件名称
        :return: 自增长序号
        """
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                current_time = datetime.now()
                sql = f"insert into {self.table_name} " \
                      f"(id, " \
                      f"deleted, " \
                      f"status, " \
                      f"creator, " \
                      f"create_time, " \
                      f"updator, " \
                      f"update_time, " \
                      f"version, " \
                      f"namespace_id, " \
                      f"name, " \
                      f"path, " \
                      f"type, " \
                      f"size, " \
                      f"remark, " \
                      f"vector_type, " \
                      f"vector_status, " \
                      f"vector_count, " \
                      f"display_name, " \
                      f"trace_name, " \
                      f"use_status) " \
                      f"values ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s');" % \
                      (file_id, '0', '0', creator, current_time, 'system', current_time, '0',
                       namespace_id, name, path, type, size, remark, 'Person', "Wait", 0, display_name, trace_name, '1')
                cursor.execute(sql)
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
        修改知识库文件信息
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
            namespace_id: str = None,
            name: str = None,
            path: str = None,
            vector_ids: str = None,
            vector_status: str = None,
    ) -> List[NamespaceFileModel]:
        """
        查询知识库文件列表信息
        :param file_id: 文件标识
        :param namespace_id: 知识库标识
        :param name: 文件名称
        :param path: 文件地址
        :param vector_ids: 向量标识
        :param vector_status: 向量状态
        :return: 知识库文件列表
        """
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                sql = f"select id, namespace_id, name, path, type, size, remark, vector_ids, " \
                      f"vector_status, vector_count, channel, deleted, creator, create_time, updator, update_time, version, " \
                      f"display_name, trace_name, md5 " \
                      f"from {self.table_name} where deleted = 0 "
                if file_id:
                    sql = sql + f" and id = '{file_id}'"
                if namespace_id:
                    sql = sql + f" and namespace_id = '{namespace_id}'"
                if name:
                    sql = sql + f" and name like '%{name}'%"
                if path:
                    sql = sql + f" and path = '{path}'"
                if vector_ids:
                    sql = sql + f" and vector_ids like '%{vector_ids}'%"
                if vector_status:
                    sql = sql + f" and vector_status = '{vector_status}'"
                cursor.execute(sql)
                data_list = cursor.fetchall()
                logger.info("Request_id={}, [{}]查询结果：{}, 数据长度：{}.", self.request_id, self.table_name, data_list,
                            len(data_list))
                result_list = []
                for data in data_list:
                    result_list.append(NamespaceFileModel(data))
                return result_list
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
        finally:
            conn.close()

    def find_by_id(
            self,
            file_id,
    ) -> NamespaceFileModel:
        """
        查询指定的知识库文件
        :param file_id: 文件标识
        :return: 文件列表
        """
        file_list = self.find_by_condition(file_id=file_id)
        return file_list[0] if len(file_list) > 0 else None

    def find_by_status_none(
            self
    ) -> List[NamespaceFileModel]:
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
                    result_list.append(NamespaceFileModel(data))
                return result_list
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
        finally:
            conn.close()

    def find_by_path(
            self,
            file_name: str,
            namespace_id: str
    ) -> NamespaceFileModel:
        """
        根据文件目录查询指定记录
        :param namespace_id: 命名空间标识
        :param file_name: 文件名称
        :return: 元文件信息
        """
        conn = get_db_conn()
        try:
            logger.info(
                f">>>>>>>>>>>>>>>>>>>>>根据文件目录查询指定记录：file_name={file_name}, namespace_id={namespace_id}")
            with conn.cursor() as cursor:
                sql = f"select id, namespace_id, name, path, type, size, remark, vector_ids, " \
                      f"vector_status, vector_count, channel, deleted, creator, create_time, updator, update_time, version, " \
                      f"display_name, trace_name, md5 " \
                      f"from {self.table_name} " \
                      f"where name = '{file_name}' and namespace_id = '{namespace_id}' ; "
                cursor.execute(sql)
                data = cursor.fetchone()
                logger.info("Request_id={}, [{}]查询结果：{}.", self.request_id, self.table_name, data)
                if data:
                    return NamespaceFileModel(data)
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
        finally:
            conn.close()

    def update_vector_ids(
            self,
            custom_id: str = None,
            file_id: str = None
    ):
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                sql = f"UPDATE {self.table_name} SET vector_ids = CONCAT(vector_ids, ',{custom_id}')" \
                      f"WHERE id = {file_id};"
                cursor.execute(sql)
            conn.commit()
            logger.info("Request_id={}, [{}]更新结果：{}.", self.request_id, self.table_name, custom_id)
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
        finally:
            conn.close()
