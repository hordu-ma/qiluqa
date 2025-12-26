from datetime import datetime
import uuid
from typing import List
import pymysql
from loguru import logger
from config.base_config import (
    MYSQL_HOST,
    MYSQL_DATABASE,
    MYSQL_CHARSET,
    MYSQL_PORT,
    MYSQL_PASSWD,
    MYSQL_USER)


class ChatHistoryFilesSummaryModel:
    """
    历史聊天记录
    """
    def __init__(
            self,
            data: tuple
    ):
        """
        构造函数
        :param data: 数据集合
        """
        self.history_id = data[0]
        self.summary = data[1]
        self.create_time = data[2]
        self.update_time = data[3]
        self.deleted = data[4]
        self.creator = data[5]
        self.updator = data[6]
    def __str__(self):
        """
        描述函数
        :return: 描述信息
        """
        return "ChatHistoryFilesSummaryModel{" \
               "'create_time': '"+str(self.create_time)+"', " \
               "'update_time': '"+str(self.update_time)+"', " \
               "'deleted': '"+str(self.deleted)+"', " \
               "'creator': '"+str(self.creator)+"', " \
               "'updator': '"+str(self.updator)+"', " \
               "'history_id': '"+str(self.history_id)+"', " \
               "'summary': '"+str(self.summary)+"', " \
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


class AiChatHistoryFilesSummaryDomain:
    """
    历史聊天附件summary记录模块
    """
    table_name: str = "ai_chat_history_files_summary"

    def __init__(
            self,
            request_id: str = str(uuid.uuid4())
    ):
        """
        构造函数
        :param request_id: 请求唯一标识
        """
        self.request_id = request_id

    def find_all_by_history_ids(
            self,
            history_ids: List[str] = [],
    ) -> List[ChatHistoryFilesSummaryModel]:
        """
        根据历史记录ids查询所有关联的summary
        :param history_ids: 历史记录ids
        :return: 历史聊天记录关联的summary列表
        """
        if not history_ids or len(history_ids) <= 0:
            return []

        conn = get_db_conn()
        try:
            # 过滤掉None和空字符串
            valid_items = [str(item) for item in history_ids if item is not None and str(item).strip()]
            sub_sql_in = "('" + "', '".join(valid_items) + "')"
            with conn.cursor() as cursor:
                sql = f"select history_id, summary, create_time, update_time, " \
                      f"deleted, creator, updator from {self.table_name} " \
                      f"where deleted = 0 and history_id in {sub_sql_in}"
                cursor.execute(sql)
                data_list = cursor.fetchall()
                logger.info("Request_id={}, [{}]查询结果：{}, 数据长度：{}.", self.request_id, self.table_name, data_list,
                            len(data_list))

                result_list = []
                for data in data_list:
                    result_list.append(ChatHistoryFilesSummaryModel(data))
                return result_list
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
        finally:
            conn.close()

    def create(
            self,
            history_id: str,
            summary: str,
            answer_time: datetime = None,
            question_time: datetime = None,
            deleted: int = 0,
    ) -> int:
        """
        创建历史聊天附件摘要记录
        :param summary: 附件摘要信息
        :param history_id: 历史记录id
        :param answer_time: 回答时间
        :param question_time: 提问时间
        :param deleted: 是否标记删除
        :return: 自增长序号
        """
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                # 设置问答时间，若未指定则默认取当前时间
                current_time = datetime.now()
                question_time = question_time or current_time
                answer_time = answer_time or current_time

                summary = summary.replace("'", "\\'")

                sql = f"insert into {self.table_name} " \
                      f"(deleted, " \
                      f"creator, " \
                      f"create_time, " \
                      f"updator, " \
                      f"update_time, " \
                      f"version, " \
                      f"history_id, " \
                      f"summary) " \
                      f"values ('%s','%s','%s','%s','%s','%s','%s','%s');" % \
                      (deleted, 'system', question_time, 'system', answer_time, '0', history_id, summary)

                cursor.execute(sql.encode('utf-8'))
                conn.commit()
                logger.info("Request_id={}, [{}]保存成功!", self.request_id, self.table_name)
                return cursor.lastrowid
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
            conn.rollback()
        finally:
            conn.close()
