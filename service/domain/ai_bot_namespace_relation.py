import uuid
from typing import List

import pymysql
from loguru import logger

from config.base_config import MYSQL_HOST, MYSQL_PORT, MYSQL_CHARSET, MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWD


class BotNamespaceRelationModel:
    """
    机器人关联知识库信息实体模型
    """
    def __init__(
            self,
            data: tuple
    ):
        """
        构造函数
        :param data: 数据集合
        """
        self.id = data[0],
        self.deleted = data[1]
        self.creator = data[2]
        self.create_time = data[3]
        self.updator = data[4]
        self.update_time = data[5]
        self.version = data[6]
        self.bot_id = data[7]
        self.nas_id = data[8]

    def __str__(self):
        return "BotNamespaceRelationModel{" \
               "'id': '" + str(self.id) + "', " \
               "'deleted': '" + str(self.deleted) + "', " \
               "'creator': '" + str(self.creator) + "', " \
               "'create_time': '" + str(self.create_time) + "', " \
               "'updator': '" + str(self.updator) + "', " \
               "'update_time': '" + str(self.update_time) + "', " \
               "'version': '" + str(self.version) + "', " \
               "'bot_id': '" + str(self.bot_id) + "', " \
               "'nas_id': '" + str(self.nas_id) + "'" \
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


class AiBotNamespaceRelationDomain:
    """
    机器人关联知识库模块
    """
    table_name: str = "ai_bot_namespace_relation"

    def __init__(
            self,
            request_id: str = str(uuid.uuid4())
    ):
        """
        构造函数
        :param request_id: 请求唯一标识
        """
        self.request_id = request_id

    def find_nas_id_by_bot_id(
            self,
            bot_id: str
    ):
        """
        根据机器人ID标识查询关联表信息
        :param bot_id: 机器人标识
        :return: BotNamespaceRelationModel_list
        """
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                sql = f"select id, deleted, creator, create_time, updator, update_time, version, " \
                      f"bot_id, nas_id " \
                      f"from {self.table_name} where bot_id = '{bot_id}' and deleted = 0"
                cursor.execute(sql)
                datas = cursor.fetchall()
                logger.info("Request_id={}, [{}]查询结果：{}.", self.request_id, self.table_name, datas)
                data_list = []
                if datas:
                    for data in datas:
                        data_list.append(str(BotNamespaceRelationModel(data).nas_id))
                    return tuple(data_list)
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
            return None
        finally:
            conn.close()


"""
data_list = []
if datas:
    for data in datas:
    data_list.append(BotNamespaceRelationModel(data))
"""