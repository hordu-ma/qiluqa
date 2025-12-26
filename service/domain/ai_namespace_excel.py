# -*- coding: utf-8 -*-
import uuid
from datetime import datetime
from typing import List

from loguru import logger
from config.base_config import *
import pymysql


class NamespaceExcelModel:
    """
    知识库关联Excel信息表
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
        self.excel_id = data[7]
        self.namespace_id = data[8]
        self.namespace_file_id = data[9]
        self.name = data[10]
        self.path = data[11]
        self.type = data[12]
        self.size = data[13]
        self.remark = data[14]
        self.channel = data[15]

    def __str__(self):
        """
        描述函数
        :return: 描述信息
        """
        return "NamespaceExcelModel{" \
               "'id': '"+str(self.id)+"', " \
               "'deleted': '"+str(self.deleted)+"', " \
               "'creator': '"+str(self.creator)+"', " \
               "'create_time': '"+str(self.create_time)+"', " \
               "'updator': '"+str(self.updator)+"', " \
               "'update_time': '"+str(self.update_time)+"', " \
               "'version': '"+str(self.version)+"', " \
               "'excel_id': '"+str(self.excel_id)+"', " \
               "'namespace_id': '"+str(self.namespace_id)+"', " \
               "'namespace_file_id': '"+str(self.namespace_file_id)+"', " \
               "'name': '"+str(self.name)+"', " \
               "'path': '"+str(self.path)+"', " \
               "'type': '"+str(self.type)+"', " \
               "'size': '"+str(self.size)+"', " \
               "'remark': '"+str(self.remark)+"', " \
               "'channel': '"+str(self.channel)+"'" \
               "}"


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


class AiNamespaceExcelDomain:
    """
    知识库关联Excel信息表
    """
    table_name: str = "ai_namespace_excel"

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
            excel_id: str,
            namespace_id: str,
            namespace_file_id: str,
            name: str,
            path: str,
            type: str,
            size: str,
            remark: str = '',
            channel: str = '',
    ) -> int:
        """
        新增记录
        :param excel_id: 文件业务标识
        :param namespace_id: 知识库空间标识
        :param namespace_file_id: 知识库文件标识
        :param name: 文件名称
        :param path: 路径
        :param type: 类型
        :param size: 大小K为单位
        :param remark: 说明
        :param channel: 文件渠道
        :return: 新增记录的主键标识
        """
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                path = path.replace("\\", "\\\\")
                current_time = datetime.now()
                sql = f"insert into {self.table_name} " \
                      f"(deleted, " \
                      f"creator, " \
                      f"create_time, " \
                      f"updator, " \
                      f"update_time, " \
                      f"version, " \
                      f"excel_id, " \
                      f"namespace_id, " \
                      f"namespace_file_id, " \
                      f"name, " \
                      f"path, " \
                      f"type, " \
                      f"size, " \
                      f"remark, " \
                      f"channel) " \
                      f"values ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s');" % \
                      ('0', 'system', current_time, 'system', current_time, '0',
                       excel_id, namespace_id, namespace_file_id, name, path, type, size, remark, channel)
                cursor.execute(sql.encode('utf-8'))
                conn.commit()
                logger.info("Request_id={}, [{}]保存成功!", self.request_id, self.table_name)
                return cursor.lastrowid
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
            return 0
        finally:
            conn.close()

    def find_by_namespace_file_id(
            self,
            namespace_id: str,
            namespace_file_id: str,
    ) -> List[NamespaceExcelModel]:
        """
        查询知识库关联Excel列表
        :param namespace_id: 知识库标识
        :param namespace_file_id: 知识库文件标识
        :return: Excel列表
        """
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                sql = f"select id, deleted, creator, create_time, updator, update_time, version, " \
                      f"excel_id, namespace_id, namespace_file_id, name, path, type, size, remark, channel " \
                      f"from {self.table_name} where namespace_id = '{namespace_id}' and namespace_file_id = '{namespace_file_id}'"
                cursor.execute(sql)
                data_list = cursor.fetchall()
                logger.info("Request_id={}, [{}]查询结果：{}, 数据长度：{}.", self.request_id, self.table_name, data_list, len(data_list))

                result_list = []
                for data in data_list:
                    result_list.append(NamespaceExcelModel(data))
                return result_list
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
        finally:
            conn.close()
