from datetime import datetime, timezone, timedelta
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
from framework.util.aes_256 import AESCipher


class ChatHistoryModel:
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
        self.question = data[0]
        self.answer = data[1]
        self.user_id = data[2]
        self.bot_id = data[3]
        self.create_time = data[4]
        self.update_time = data[5]
        self.deleted = data[6]
        self.creator = data[7]
        self.updator = data[8]
        self.answer_like = data[9]
        self.group_uuid = data[10]
        self.answer_type = data[11]
        self.comment = data[12]
        self.use_send = data[13]
        self.use_mark = data[14]
        self.thinking = data[15]
        self.search = data[16]
        self.files = data[17]
        self.id = data[18]

    def __str__(self):
        """
        描述函数
        :return: 描述信息
        """
        return "ChatHistoryModel{" \
               "'question': '"+str(self.question)+"', " \
               "'answer': '"+str(self.answer)+"', " \
               "'user_id': '"+str(self.user_id)+"', " \
               "'bot_id': '"+str(self.bot_id)+"', " \
               "'create_time': '"+str(self.create_time)+"', " \
               "'update_time': '"+str(self.update_time)+"', " \
               "'deleted': '"+str(self.deleted)+"', " \
               "'creator': '"+str(self.creator)+"', " \
               "'updator': '"+str(self.updator)+"', " \
               "'answer_like': '"+str(self.answer_like)+"', " \
               "'group_uuid': '"+str(self.group_uuid)+"', " \
               "'answer_type': '"+str(self.answer_type)+"', " \
               "'comment': '"+str(self.comment)+"', " \
               "'use_send': '"+str(self.use_send)+"', " \
               "'use_mark': '"+str(self.use_mark)+"'" \
               "'thinking': '"+str(self.thinking)+"'" \
               "'search': '"+str(self.search)+"'" \
               "'files': '"+str(self.files)+"'" \
               "'id': '"+str(self.id)+"'" \
               "}"


def get_db_conn():
    """
    获取数据库连接对象
    :return: conn数据库连接对象
    """
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=int(MYSQL_PORT),
        database=MYSQL_DATABASE,
        charset=MYSQL_CHARSET,
        user=MYSQL_USER,
        passwd=MYSQL_PASSWD
    )
    # 设置连接时区为北京时间（UTC+8）
    with conn.cursor() as cursor:
        cursor.execute("SET time_zone = '+8:00'")
    return conn


class AiChatHistoryDomain:
    """
    历史聊天记录模块
    """
    table_name: str = "ai_chat_history"

    def __init__(
            self,
            request_id: str = str(uuid.uuid4())
    ):
        """
        构造函数
        :param request_id: 请求唯一标识
        """
        self.request_id = request_id

    def find_all_by_id(
            self,
            user_id: str,
            bot_id: str,
    ) -> List[ChatHistoryModel]:
        """
        根据用户标识查询所有历史
        :param user_id: 用户标识
        :param bot_id: 机器人标识
        :return: 历史聊天记录列表
        """
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                sql = f"select question, answer, user_id, bot_id, create_time, update_time, " \
                      f"deleted, creator, updator, answer_like, group_uuid, answer_type, comment, " \
                      f"use_send, use_mark, thinking, `search`, files,id from {self.table_name} " \
                      f"where deleted = 0 and bot_id = '{bot_id}' and user_id = '{user_id}'"
                cursor.execute(sql)
                data_list = cursor.fetchall()
                logger.info("Request_id={}, [{}]查询结果：{}, 数据长度：{}.", self.request_id, self.table_name, data_list,
                            len(data_list))

                result_list = []
                for data in data_list:
                    historyModel = ChatHistoryModel(data)
                    # 问题解密
                    historyModel.question = AESCipher().aes_decoding(historyModel.question)
                    historyModel.answer = AESCipher().aes_decoding(historyModel.answer)
                    result_list.append(historyModel)
                return result_list
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
        finally:
            conn.close()

    def find_last_by_id(
            self,
            user_id: str,
            bot_id: str = None,
            group_uuid: str = None,
            limit_size: int = 3
    ) -> List[ChatHistoryModel]:
        """
        根据用户标识查询最近指定范围历史记录
        :param user_id: 用户标识
        :param bot_id: 机器人标识
        :param group_uuid: 会话标识
        :param limit_size: 指定范围
        :return: 历史聊天记录Model
        """
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                sql = f"select question, answer, user_id, bot_id, create_time, update_time, " \
                      f"deleted, creator, updator, answer_like, group_uuid, answer_type, comment, " \
                      f"use_send, use_mark, thinking, `search`, files, id from {self.table_name} " \
                      f"where deleted = 0 and (answer_like is null or answer_like = 'LIKE') and user_id = '{user_id}' "
                if bot_id:
                    sql = sql + f" and bot_id = '{bot_id}' "
                if group_uuid:
                    sql = sql + f" and group_uuid = '{group_uuid}' "
                sql = sql + f" order by create_time desc limit {limit_size};"
                cursor.execute(sql)
                data_list = cursor.fetchall()
                logger.info("Request_id={}, [{}]查询结果：{}, 数据长度：{}.", self.request_id, self.table_name, data_list,
                            len(data_list))

                result_list = []
                for data in data_list:
                    historyModel = ChatHistoryModel(data)
                    # 问题解密
                    historyModel.question = AESCipher().aes_decoding(historyModel.question)
                    historyModel.answer = AESCipher().aes_decoding(historyModel.answer)
                    result_list.append(historyModel)
                return result_list
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
        finally:
            conn.close()

    def create(
            self,
            user_id: str,
            bot_id: str,
            question: str,
            answer: str,
            answer_time: datetime = None,
            question_time: datetime = None,
            deleted: int = 0,
            group_uuid: str = None,
            answer_type: str = None,
            comment: str = None,
            use_send: int = 0,
            use_mark: str = None,
            llms: str = "",
            llms_model_name: str = "",
            total_tokens: int = 0,
            input_tokens: int = 0,
            output_tokens: int = 0,
            thinking: str = None,
            search: str = None,
            files: str = None,
            voice: int = 0,
    ) -> int:
        """
        创建历史聊天记录
        :param voice:是否语音输入：0-否，1-是。默认非语音输入
        :param user_id: 用户标识信息
        :param bot_id: 机器人标识信息
        :param question: 提问
        :param answer: 回答
        :param answer_time: 回答时间
        :param question_time: 提问时间
        :param deleted: 是否标记删除
        :param group_uuid: 会话分组标识
        :param answer_type: 回答形式
        :param comment: 评论
        :param use_send: 是否使用并发送给用户
        :param use_mark: 关联用户的使用标签信息
        :param llms: 大语言模型平台
        :param llms_model_name: 子模型名称
        :param total_tokens: Token总消耗量
        :param input_tokens: Token输入消耗量
        :param output_tokens: Token输出消耗量
        :param thinking: 深度思考过程文本
        :param search: 联网搜索内容
        :param files: 聊天附件信息
        :return: 自增长序号
        """
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                # 设置问答时间，若未指定则默认取当前北京时间（UTC+8）
                beijing_tz = timezone(timedelta(hours=8))
                current_time = datetime.now(beijing_tz).replace(tzinfo=None)
                logger.info("Request_id={}, 当前北京时间: {}", self.request_id, current_time)
                
                # 如果传入的时间没有时区信息，假设为北京时间
                if question_time is None:
                    question_time = current_time
                elif question_time.tzinfo is not None:
                    # 如果有时区信息，转换为北京时间
                    question_time = question_time.astimezone(beijing_tz).replace(tzinfo=None)
                else:
                    # 如果没有时区信息，假设是UTC时间，转换为北京时间
                    question_time = question_time + timedelta(hours=8)
                
                if answer_time is None:
                    answer_time = current_time
                elif answer_time.tzinfo is not None:
                    # 如果有时区信息，转换为北京时间
                    answer_time = answer_time.astimezone(beijing_tz).replace(tzinfo=None)
                else:
                    # 如果没有时区信息，假设是UTC时间，转换为北京时间
                    answer_time = answer_time + timedelta(hours=8)
                
                logger.info("Request_id={}, 存储的question_time: {}, answer_time: {}", self.request_id, question_time, answer_time)

                answer = answer.replace("'", "\\'")
                question = question.replace("'", "\\'")

                sql = f"insert into {self.table_name} " \
                      f"(deleted, " \
                      f"creator, " \
                      f"create_time, " \
                      f"updator, " \
                      f"update_time, " \
                      f"version, " \
                      f"user_id, " \
                      f"bot_id, " \
                      f"question, " \
                      f"answer, " \
                      f"group_uuid, " \
                      f"answer_type, " \
                      f"comment, " \
                      f"use_send, " \
                      f"use_mark, " \
                      f"llms, " \
                      f"llms_model_name, " \
                      f"total_tokens, " \
                      f"input_tokens, " \
                      f"output_tokens, " \
                      f"thinking, " \
                      f"`search`, " \
                      f"voice, " \
                      f"files) " \
                      f"values ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s');" % \
                      (deleted, 'system', question_time, 'system', answer_time, '0', user_id, bot_id, AESCipher().aes_encoding(question),
                       AESCipher().aes_encoding(answer), group_uuid, answer_type, comment, use_send, use_mark, llms, llms_model_name, total_tokens,
                       input_tokens, output_tokens, thinking, search, voice, files)

                cursor.execute(sql.encode('utf-8'))
                conn.commit()
                logger.info("Request_id={}, [{}]保存成功!", self.request_id, self.table_name)
                return cursor.lastrowid
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
            conn.rollback()
        finally:
            conn.close()
