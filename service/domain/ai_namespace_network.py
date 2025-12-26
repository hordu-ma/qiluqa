import uuid
from datetime import datetime
from typing import List

import pymysql
from loguru import logger
from config.base_config import MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, MYSQL_CHARSET, MYSQL_USER, MYSQL_PASSWD, \
    SCHEDULES_FILE_RETRY_COUNT, SCHEDULES_FILE_LIMIT_COUNT, SPLIT_CHUNK_SIZE, SPLIT_CHUNK_OVERLAP, PAGE_SIZE


class NameSpaceNetworkModel:
    """
    知识库爬虫实体模型
    """
    def __init__(
            self,
            data: tuple,
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
        self.namespace_id = data[7]
        self.file_id = data[8]
        self.website = data[9]
        self.title = data[10]
        self.update_rate = data[11]
        self.last_time = data[12]
        self.next_time = data[13]
        self.type = data[14]
        self.status = data[15]
        self.retry_count = data[16]
        self.result_code = data[17]
        self.result_msg = data[18]

    def __str__(self):
        """
        描述函数
        :return: 描述信息
        """
        return "NameSpaceNetworkModel{" \
               "'id': '"+str(self.id)+"', " \
               "'deleted': '"+str(self.deleted)+"', " \
               "'creator': '"+str(self.creator)+"', " \
               "'create_time': '"+str(self.create_time)+"', " \
               "'updator': '"+str(self.updator)+"', " \
               "'update_time': '"+str(self.update_time)+"', " \
               "'version': '"+str(self.version)+"', " \
               "'file_id': '"+str(self.file_id)+"', " \
               "'namespace_id': '"+str(self.namespace_id)+"', " \
               "'website': '"+str(self.website)+"', " \
               "'title': '"+str(self.title)+"', " \
               "'update_rate': '"+str(self.update_rate)+"', " \
               "'last_time': '"+str(self.last_time)+"', " \
               "'next_time': '"+str(self.next_time)+"', " \
               "'type': '" + str(self.type) + "', " \
               "'status': '" + str(self.status) + "', " \
               "'retry_count': '" + str(self.retry_count) + "', " \
               "'result_code': '" + str(self.result_code) + "', " \
               "'result_msg': '" + str(self.result_msg)+"'}"

    def default_serializer(self) -> dict:
        if isinstance(self, NameSpaceNetworkModel):
            return {
                'id': self.id,
                'deleted': self.deleted,
                'creator': str(self.creator),
                'createTime': str(self.create_time),
                'updator': self.updator,
                'updateTime': str(self.update_time),
                'version': self.version,
                'file_id': self.file_id,
                'namespace_id': str(self.namespace_id),
                'website': str(self.website),
                'title': str(self.title),
                'update_rate': self.update_rate,
                'last_time': str(self.last_time),
                'next_time': str(self.next_time),
                'type': self.type,
                'status': self.status,
                'retry_count': str(self.retry_count),
                'result_code': str(self.result_code),
                'result_msg': str(self.result_msg)
            }
        raise TypeError("Not serializable")


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


class AiNamespaceNetworkDomain:
    """
    知识库爬虫信息模块
    """
    table_name: str = "ai_namespace_file_network"

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
            id: str,
            deleted: str,
            creator: str,
            create_time: str,
            updator: str,
            update_time: str,
            version: str,
            file_id: str = None,
            namespace_id: str = None,
            website: str = None,
            title: str = None,
            update_rate: str = None,
            last_time: str = None,
            next_time: str = None,
            type: str = None,
            status: str = None,
            retry_count: str = None,
            result_code: str = None,
            result_msg: str = None
    ) -> int:
        """
        创建知识库文件信息
        :param id: 网站标识
        :param deleted: 是否删除
        :param namespace_id: 知识库标识
        :param creator: 创建者名称
        :param create_time: 创建时间
        :param updator: 更新者名称
        :param update_time: 更新时间
        :param version: 版本
        :param file_id: 文件id信息
        :param website: 爬取网站信息
        :param title: 网站名称
        :param update_rate: 网页信息更新速度
        :param last_time: 上次更新时间
        :param next_time: 下次更新时间
        :param type: 任务类型
        :param status: 执行状态
        :param retry_count: 重试次数
        :param result_code: 最后一次执行状态码
        :param result_msg: 最后一次执行状态描述
        :return: 自增长序号
        """
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                current_time = datetime.now()
                sql = f"insert into {self.table_name} " \
                      f"(id, " \
                      f"deleted, " \
                      f"creator, " \
                      f"create_time, " \
                      f"updator, " \
                      f"update_time, " \
                      f"version, " \
                      f"namespace_id, " \
                      f"file_id, " \
                      f"website, " \
                      f"title, " \
                      f"update_rate, " \
                      f"last_time, " \
                      f"next_time, " \
                      f"type, " \
                      f"status, " \
                      f"retry_count, " \
                      f"result_code, " \
                      f"result_msg, " \
                      f"values ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s');" % \
                      (id, deleted, creator, create_time, updator, update_time, version, namespace_id,
                       file_id, website, title, update_rate, last_time, next_time, type, status,
                       retry_count, result_code, result_msg)
                cursor.execute(sql.encode('utf-8'))
                conn.commit()
                logger.info("Request_id={}, [{}]保存成功!", self.request_id, self.table_name)
                return cursor.lastrowid
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
            return 0
        finally:
            conn.close()

    def find_by_url_id(
            self,
            url_id: str = None
    ) -> NameSpaceNetworkModel:
        """
        查询爬虫网站信息
        :param url_id: 网站标识
        :return: 爬虫网站列表
        """
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                sql = f"select id, deleted, creator, create_time, updator, update_time, version, namespace_id, " \
                      f"file_id, website, title, update_rate, last_time, next_time, type, status, " \
                      f"retry_count, result_code, result_msg " \
                      f"from {self.table_name} where deleted = 0 and id = {url_id}"
                cursor.execute(sql)
                data = cursor.fetchone()
                data = NameSpaceNetworkModel(data)
                return data
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
        finally:
            conn.close()

    def find_all_update_network(
            self
    ) -> list[NameSpaceNetworkModel]:
        """
        查询知爬虫网站列表信息
        :return: 爬虫网站列表
        """
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) from {self.table_name} WHERE deleted = 0 and type = 1")
                total_rows = cursor.fetchone()[0]
                total_pages = (total_rows // PAGE_SIZE) + (1 if total_rows % PAGE_SIZE > 0 else 0)
                for current_page in range(total_pages):
                    offset = current_page * PAGE_SIZE
                    sql = f"select id, deleted, creator, create_time, updator, update_time, version, namespace_id, " \
                          f"file_id, website, title, update_rate, last_time, next_time, type, status, " \
                          f"retry_count, result_code, result_msg " \
                          f"from {self.table_name} where deleted = 0 and type = 1 ORDER BY create_time " \
                          f"LIMIT {PAGE_SIZE} OFFSET {offset}"
                    cursor.execute(sql)
                    datas = cursor.fetchall()
                    result_list = []
                    for data in datas:
                        data = NameSpaceNetworkModel(data)
                        result_list.append(data)
                    return result_list
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
        finally:
            conn.close()

    def set_network_file_id(
            self,
            file_id: str,
            network_model: NameSpaceNetworkModel
    ):
        """
        保存关联网站文件信息
        """
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                sql = f"update {self.table_name} set " \
                      f"file_id = {file_id}" \
                      f"where id={network_model.id}; "
                cursor.execute(sql)
            conn.commit()
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
        finally:
            conn.close()

    def update_next_time(
            self,
            network_model: NameSpaceNetworkModel
    ):
        """
        更新下次爬虫时间
        """
        conn = get_db_conn()
        try:
            next_time = network_model.next_time + network_model.update_rate
            with conn.cursor() as cursor:
                sql = f"update {self.table_name} set " \
                      f"next_time = {next_time}" \
                      f"where id={network_model.id}; "
                cursor.execute(sql)
            conn.commit()
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
        finally:
            conn.close()
