import uuid
from datetime import datetime
from typing import List
import pymysql
from loguru import logger
from config.base_config import MYSQL_HOST, MYSQL_DATABASE, MYSQL_PORT, MYSQL_CHARSET, MYSQL_USER, MYSQL_PASSWD


class ChatImagesModel:

    def __init__(
            self,
            data: tuple
    ):
        self.id = data[0]
        self.deleted = data[1]
        self.creator = data[2]
        self.create_time = data[3]
        self.updator = data[4]
        self.update_time = data[5]
        self.version = data[6]
        self.user_id = data[7]
        self.source = data[8]
        self.target = data[9]
        self.answer_like = data[10]
        self.num = data[11]
        self.uuid = data[12]
        self.style = data[13]
        self.model = data[14]
        self.dir = data[15]
        self.status = data[16]

    def __str__(self):
        """
        描述函数
        :return: 描述信息
        """
        return "ChatImagesModel{" \
               "'id': '"+str(self.id)+"', " \
               "'deleted': '"+str(self.deleted)+"', " \
               "'creator': '"+str(self.creator)+"', " \
               "'create_time': '"+str(self.create_time)+"', " \
               "'updator': '"+str(self.updator)+"', " \
               "'update_time': '"+str(self.update_time)+"', " \
               "'version': '"+str(self.version)+"', " \
               "'user_id': '"+str(self.user_id)+"', " \
               "'source': '"+str(self.source)+"', " \
               "'target': '"+str(self.target)+"', " \
               "'answer_like': '"+str(self.answer_like)+"', " \
               "'num': '"+str(self.num)+"', " \
               "'uuid': '"+str(self.uuid)+"', " \
               "'style': '"+str(self.style)+"', " \
               "'model': '"+str(self.model)+"', " \
               "'dir': '"+str(self.dir)+"', " \
               "'status': '"+str(self.status)+"'" \
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


class AiChatImagesDomain:
    table_name: str = "ai_chat_images"

    def __init__(
            self,
            request_id: str = str(uuid.uuid4())
    ):
        self.request_id = request_id

    def find_by_id(
            self,
            images_id: str
    ) -> ChatImagesModel:
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                sql = f"select id, deleted, creator, create_time, updator, update_time, version, " \
                      f"user_id, source, target, answer_like, num, uuid, style, model, dir, status " \
                      f"from {self.table_name} where id = '{images_id}'"
                cursor.execute(sql)
                data = cursor.fetchone()
                logger.info("Request_id={}, [{}]查询结果：{}.", self.request_id, self.table_name, data)
                if data:
                    return ChatImagesModel(data)
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
        finally:
            conn.close()

    def update(
            self,
            images_id: str,
            images_status: str,
            images_uuid: str,
            deleted: int = 0,
            targets: List[str] = None,
    ):
        conn = get_db_conn()
        try:
            targets = targets if targets else []
            with conn.cursor() as cursor:
                current_time = datetime.now()
                sql = f"update {self.table_name} set " \
                      f"deleted = '{deleted}', " \
                      f"updator = 'system', " \
                      f"update_time = '{current_time}', " \
                      f"status = '{images_status}', " \
                      f"uuid = '{images_uuid}', " \
                      f"target = '{','.join(targets)}' " \
                      f"where id={images_id}; "
                cursor.execute(sql.encode('utf-8'))
                conn.commit()
                logger.info("Request_id={}, [{}]修改成功!", self.request_id, self.table_name)
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
        finally:
            conn.close()
