import uuid
from typing import List

from loguru import logger
from config.base_config import *
import pymysql


class DisclaimerModel:
    """
    禁用词信息表对象
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
        self.text = data[7]
        self.namespace_id = data[8]
        self.has_trace_flag = data[9]
        self.random_weight = data[10]
        self.source_channel = data[11]

    def __str__(self):
        """
        描述函数
        :return: 描述信息
        """
        return "DisclaimerModel{" \
               "'id': '" + str(self.id) + "', " \
               "'deleted': '" + str(self.deleted) + "', " \
               "'creator': '" + str(self.creator) + "', " \
               "'create_time': '" + str(self.create_time) + "', " \
               "'updator': '" + str(self.updator) + "', " \
               "'update_time': '" + str(self.update_time) + "', " \
               "'version': '" + str(self.version) + "', " \
               "'text': '" + str(self.text) + "', " \
               "'namespace_id': '" + str(self.namespace_id) + "', " \
               "'has_trace_flag': '" + str(self.has_trace_flag) + "', " \
               "'random_weight': '" + str(self.random_weight) + "', " \
               "'source_channel': '" + str(self.source_channel) + "}"

    def default_serializer(self) -> dict:
        if isinstance(self, DisclaimerModel):
            return {
                'id': self.id,
                'deleted': self.deleted,
                'creator': str(self.creator),
                'createTime': str(self.create_time),
                'updator': self.updator,
                'updateTime': str(self.update_time),
                'version': self.version,
                'text': str(self.text),
                'namespace_id': str(self.namespace_id),
                'has_trace_flag': str(self.has_trace_flag),
                'random_weight': str(self.random_weight),
                'source_channel': str(self.source_channel)
            }
        raise TypeError("Not serializable")

    def if_has_trace_flag(self):
        return self.has_trace_flag == '1'


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


class AiDisclaimerDomain:
    """
    查询免责声明表
    """
    table_name: str = "ai_disclaimer"

    def __init__(
            self,
            request_id: str = str(uuid.uuid4())
    ):
        """
        构造函数
        :param request_id: 请求唯一标识
        """
        self.request_id = request_id

    def find_all(
            self,
    ) -> List[DisclaimerModel]:
        """
        查询ai_prohibited表中的所有数据
        按主键id查询
        返回值放进列表中
        """
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                sql = f"select id, deleted, creator, create_time, updator, update_time, version, " \
                      f"text, namespace_id, has_trace_flag,random_weight, source_channel " \
                      f"from {self.table_name} where deleted = 0 order by update_time "
                cursor.execute(sql)
                data_list = cursor.fetchall()
                logger.info("Request_id={}, [{}]查询结果：{}, 数据长度：{}.", self.request_id, self.table_name, data_list, len(data_list))
                result_list = []
                for data in data_list:
                    result_list.append(DisclaimerModel(data))
                return result_list
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
        finally:
            conn.close()
