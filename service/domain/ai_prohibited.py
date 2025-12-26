# -*- coding: utf-8 -*-
import uuid
from typing import List

from loguru import logger
from config.base_config import *
import pymysql


class ProhibitedModel:
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
        self.prohibited = data[7]
        self.rule_type = data[8]
        self.rule_version = data[9]
        self.regular_expression = data[10]
        self.replacement = data[11]
        self.sence = data[12]

    def if_type_1_replace(self):
        return self.rule_type == "1"

    def __str__(self):
        """
        描述函数
        :return: 描述信息
        """
        return "ProhibitedModel{" \
               "'id': '"+str(self.id)+"', " \
               "'deleted': '"+str(self.deleted)+"', " \
               "'creator': '"+str(self.creator)+"', " \
               "'create_time': '"+str(self.create_time)+"', " \
               "'updator': '"+str(self.updator)+"', " \
               "'update_time': '"+str(self.update_time)+"', " \
               "'version': '"+str(self.version)+"', " \
               "'prohibited': '"+str(self.prohibited)+"', " \
               "'rule_type': '"+str(self.rule_type)+"', " \
               "'rule_version': '"+str(self.rule_version)+"', " \
               "'regular_expression': '"+str(self.regular_expression)+"', " \
               "'replacement': '"+str(self.replacement)+"', " \
               "'sence': '"+str(self.sence) + "}"

    def default_serializer(self) -> dict:
        if isinstance(self, ProhibitedModel):
            return {
                'id': self.id,
                'deleted': self.deleted,
                'creator': str(self.creator),
                'createTime': str(self.create_time),
                'updator': self.updator,
                'updateTime': str(self.update_time),
                'version': self.version,
                'prohibited': self.prohibited,
                'ruleType': str(self.rule_type),
                'ruleVersion':self.rule_version,
                'regularExpression': str(self.regular_expression),
                'replacement': self.replacement,
                'sence': str(self.sence),
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


class AiProhibitedDomain:
    """
    查询敏感禁用词信息表
    """
    table_name: str = "ai_prohibited"

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
    ) -> List[ProhibitedModel]:
        """
        查询ai_prohibited表中的所有数据
        按主键id查询
        返回值放进列表中
        """
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                sql = f"select id, deleted, creator, create_time, updator, update_time, version, " \
                      f"prohibited, rule_type, rule_version,regular_expression, replacement, sence, rsv2, rsv3 " \
                      f"from {self.table_name} where deleted = 0 order by update_time"
                cursor.execute(sql)
                data_list = cursor.fetchall()
                logger.info("Request_id={}, [{}]查询结果：{}, 数据长度：{}.", self.request_id, self.table_name, data_list, len(data_list))
                result_list = []
                for data in data_list:
                    result_list.append(ProhibitedModel(data))
                return result_list
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
        finally:
            conn.close()
