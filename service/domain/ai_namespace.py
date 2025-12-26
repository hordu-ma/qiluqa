import uuid
from typing import List
from loguru import logger
import pymysql
from config.base_config import MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, MYSQL_CHARSET, MYSQL_USER, MYSQL_PASSWD
from service.domain.ai_bot_namespace_relation import BotNamespaceRelationModel


class NamespaceModel:
    """
    知识库实体模型
    """
    CONSTANTS_PERMANENT = 0  # 长期
    CONSTANTS_TEMPORARY = 1  # 临时
    CONSTANTS_PREPARE = 2    # 预制

    def __init__(
            self,
            data: tuple
    ):
        """
        构造函数
        :param data: 数据集合
        """
        self.namespace = data[0]
        self.name = data[1]
        self.remark = data[2]
        self.chunk_size = data[3]
        self.chunk_overlap = data[4]
        self.type = data[5]
        self.user_id = data[6]
        self.id = data[7]
        self.deleted = data[8]
        self.creator = data[9]
        self.create_time = data[10]
        self.updator = data[11]
        self.update_time = data[12]
        self.version = data[13]

    def __str__(self):
        """
        描述函数
        :return: 描述信息
        """
        return "NamespaceModel{" \
               "'namespace': '"+str(self.namespace)+"', " \
               "'name': '"+str(self.name)+"', " \
               "'remark': '"+str(self.remark)+"', " \
               "'chunk_size': '"+str(self.chunk_size)+"', " \
               "'chunk_overlap': '"+str(self.chunk_overlap)+"', " \
               "'type': '"+str(self.type)+"', " \
               "'user_id': '"+str(self.user_id)+"', " \
               "'id': '"+str(self.id)+"', " \
               "'deleted': '"+str(self.deleted)+"', " \
               "'creator': '"+str(self.creator)+"', " \
               "'create_time': '"+str(self.create_time)+"', " \
               "'updator': '"+str(self.updator)+"', " \
               "'update_time': '"+str(self.update_time)+"', " \
               "'version': '"+str(self.version)+"'" \
               "}"

    def is_permanent_type(self):
        """
        是否为长期知识库
        :return: 识别结果
        """
        return self.type == self.CONSTANTS_PERMANENT

    def is_temporary_type(self):
        """
        是否为临时知识库
        :return: 识别结果
        """
        return self.type == self.CONSTANTS_TEMPORARY

    def is_prepare_type(self):
        """
        是否为Q&A知识库
        :return: 识别结果
        """
        return self.type == self.CONSTANTS_PREPARE



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


class AiNamespaceDomain:
    """
    知识库模块
    """
    table_name: str = "ai_namespace"

    def __init__(
            self,
            request_id: str = str(uuid.uuid4())
    ):
        """
        构造函数
        :param request_id: 请求唯一标识
        """
        self.request_id = request_id

    def find_by_id(
            self,
            namespace_id: str
    ):
        """
        根据标识查询知识库信息
        :param namespace_id: 知识库/命名空间标识
        :return: 知识库Model
        """
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                sql = f"select namespace, name, remark, chunk_size, chunk_overlap, type, user_id, " \
                      f"id, deleted, creator, create_time, updator, update_time, version " \
                      f"from {self.table_name} where id = '{namespace_id}'"
                cursor.execute(sql)
                data = cursor.fetchone()
                logger.info("Request_id={}, [{}]查询结果：{}.", self.request_id, self.table_name, data)
                if data:
                    return NamespaceModel(data)
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
            return None
        finally:
            conn.close()

    def find_all(
            self,
            id: str = None,
            user_id: str = None,
            type: str = None,
            name: str = None,
            namespace: str = None,
    ) -> List[NamespaceModel]:
        """
        查询全部知识库列表
        :param id: 主键标识
        :param user_id: 专属用户
        :param type: 知识库类型
        :param name: 知识库名称
        :param namespace: 知识库空间
        :return: 知识库列表
        """
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                sql = f"select namespace, name, remark, chunk_size, chunk_overlap, type, user_id, " \
                      f"id, deleted, creator, create_time, updator, update_time, version " \
                      f"from {self.table_name} where deleted = 0"
                if id:
                    sql = sql + f" and id = '{id}'"
                if user_id:
                    sql = sql + f" and user_id = '{user_id}'"
                if type:
                    sql = sql + f" and type = '{type}'"
                if name:
                    sql = sql + f" and name = '{name}'"
                if namespace:
                    sql = sql + f" and namespace = '{namespace}'"
                cursor.execute(sql)
                data_list = cursor.fetchall()
                logger.info("Request_id={}, [{}]查询结果：{}.", self.request_id, self.table_name, data_list)
                result_list = []
                for data in data_list:
                    result_list.append(NamespaceModel(data))
                return result_list
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
        finally:
            conn.close()

    def find_namespace_by_list_id(
            self,
            botNamespace_tuple: tuple[str]
    ):
        """
        根据知识库ID查询知识库信息
        :param botNamespace_tuple: 知识库/命名空间标识列表
        :return: namespace_list
        """
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                sql = f"select namespace, name, remark, chunk_size, chunk_overlap, type, user_id, " \
                      f"id, deleted, creator, create_time, updator, update_time, version " \
                      f"from {self.table_name} where "
                if len(botNamespace_tuple) == 1:
                    sql = sql + f" id = '{botNamespace_tuple[0]}'"
                else:
                    sql = sql + f" id in {botNamespace_tuple}"
                cursor.execute(sql)
                datas = cursor.fetchall()
                logger.info("Request_id={}, [{}]查询结果：{}.", self.request_id, self.table_name, datas)
                namespace_list = []
                for data in datas:
                    namespace_list.append(NamespaceModel(data))
                return namespace_list
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
            return None
        finally:
            conn.close()