import uuid
from datetime import datetime
from typing import List
from loguru import logger
from config.base_config import *
import pymysql
import json


class ChatBotModel:
    """
    机器人实体模型
    """
    CONSTANTS_BOT_MASTER = "Master"  # 主机器人
    CONSTANTS_BOT_SLAVER = "Slave"   # 从机器人
    CONSTANTS_PRIVATE_BOT = 0      # 领域问答机器人
    CONSTANTS_PUBLIC_BOT = 1       # 公共问答机器人
    CONSTANTS_PROMPT_ABILITY = 1    # 开启无分片提示词
    CONSTANTS_CHAINS_STUFF = "stuff"
    CONSTANTS_CHAINS_REFINE = "refine"

    def __init__(
            self,
            data: tuple
    ):
        """
        构造函数
        :param data: 数据集合
        """
        self.bot_id = data[0]
        self.prompt = data[1]
        self.prompt_variables = data[8]
        self.prefix_prompt = data[9]
        self.prefix_prompt_variables = data[10]
        self.namespace_id = data[2]
        self.name = data[3]
        self.memory_limit_size = data[4]
        self.welcome_tip = data[5]
        self.vector_top_k = data[6]
        self.chains_chunk_type = data[7]
        self.bot_type = data[11]
        self.slave_bot_mark = data[12]
        self.fixed_ques = data[13]
        self.use_type = data[14]
        self.suffix_prompt = data[15]
        self.id = data[16]
        self.deleted = data[17]
        self.creator = data[18]
        self.create_time = data[19]
        self.updator = data[20]
        self.update_time = data[21]
        self.version = data[22]
        self.traceability = data[23]
        self.origin_domain = data[24]
        self.fragmented_relationship = data[25]
        self.slave_carrying_question = data[26]
        self.llms = data[27]
        self.llms_base = data[28]
        self.suffix_prompt_variables = data[29]
        self.prompt_ability = data[30]
        self.bot_role = data[31]
        self.llms_models = data[32]

    def __str__(self):
        """
        描述函数
        :return: 描述信息
        """
        return "ChatBotModel{" \
               "'bot_id': '"+str(self.bot_id)+"', " \
               "'prompt': '"+str(self.prompt)+"', " \
               "'prompt_variables': '"+str(self.prompt_variables)+"', " \
               "'prefix_prompt': '"+str(self.prefix_prompt)+"', " \
               "'prefix_prompt_variables': '"+str(self.prefix_prompt_variables)+"', " \
               "'namespace_id': '"+str(self.namespace_id)+"', " \
               "'name': '"+str(self.name)+"', " \
               "'memory_limit_size': '"+str(self.memory_limit_size)+"', " \
               "'welcome_tip': '"+str(self.welcome_tip)+"', " \
               "'vector_top_k': '"+str(self.vector_top_k)+"', " \
               "'chains_chunk_type': '"+str(self.chains_chunk_type)+"', " \
               "'bot_type': '"+str(self.bot_type)+"', " \
               "'slave_bot_mark': '"+str(self.slave_bot_mark)+"', " \
               "'fixed_ques': '"+str(self.fixed_ques)+"', " \
               "'use_type': '"+str(self.use_type)+"', " \
               "'suffix_prompt': '"+str(self.suffix_prompt)+"', " \
               "'id': '"+str(self.id)+"', " \
               "'deleted': '"+str(self.deleted)+"', " \
               "'creator': '"+str(self.creator)+"', " \
               "'create_time': '"+str(self.create_time)+"', " \
               "'updator': '"+str(self.updator)+"', " \
               "'update_time': '"+str(self.update_time)+"', " \
               "'version': '"+str(self.version)+"', " \
               "'traceability': '" + str(self.traceability) + "', " \
               "'origin_domain': '" + str(self.origin_domain) + "', " \
               "'fragmented_relationship': '" + str(self.fragmented_relationship) + "', "\
               "'slave_carrying_question': '" + str(self.slave_carrying_question) + "', "\
               "'llms': '" + str(self.llms) + "', " \
               "'llms_base': '" + str(self.llms_base) + "', " \
               "'suffix_prompt_variables': '" + str(self.suffix_prompt_variables) + "', " \
               "'bot_role': '" + str(self.bot_role) + "', " \
               "'llms_models': '" + str(self.llms_models) + "', " \
               "'prompt_ability': '" + str(self.prompt_ability) + "'" \
               "}"

    def is_master_type(self):
        """
        是否为主机器人
        :return: 识别结果
        """
        return self.bot_type == self.CONSTANTS_BOT_MASTER

    def is_stuff_chains(self):
        """
        是否 Stuff 类型的聊天链
        :return: 识别结果
        """
        return self.chains_chunk_type == self.CONSTANTS_CHAINS_STUFF

    def is_refine_chains(self):
        """
        是否 Refine 类型的聊天链
        :return: 识别结果
        """
        return self.chains_chunk_type == self.CONSTANTS_CHAINS_REFINE

    def is_public_bot(self):
        """
        是否为公共问答机器人
        :return: 识别结果
        """
        return self.use_type == self.CONSTANTS_PUBLIC_BOT

    def is_private_bot(self):
        """
        是否为领域问答机器人
        :return: 识别结果
        """
        return self.use_type == self.CONSTANTS_PRIVATE_BOT

    def get_llm_model_name(self):
        """
        获取子模型名称
        """
        llms_base = json.loads(self.llms_base)
        return llms_base["modelName"] if llms_base else None

    def is_open_second_prompt(self):
        """
        是否开启召回分片信息
        :return: 识别结果
        """
        return self.prompt_ability == self.CONSTANTS_PROMPT_ABILITY


def chatbot_has_traceability(self):
    """
    判断机器人是否开启溯源免责功能
    :return: 识别结果
    """
    return self.traceability == 1


def get_db_conn():
    """
    获取数据库连接对象
    :return: conn数据库连接对象
    """
    logger.info(f"MYSQL_CHARSET={MYSQL_CHARSET},MYSQL_HOST={MYSQL_HOST}")
    return pymysql.connect(
        host=MYSQL_HOST,
        port=int(MYSQL_PORT),
        database=MYSQL_DATABASE,
        charset=MYSQL_CHARSET,
        user=MYSQL_USER,
        passwd=MYSQL_PASSWD
    )


class AiChatBotDomain:
    """
    机器人模块
    """
    table_name: str = "ai_chat_bot"

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
            id: str = None,
            bot_id: str = None,
    ) -> List[ChatBotModel]:
        """
        查询所有机器人列表
        :param id: 主键标识
        :param bot_id: 机器人标识
        :return: 机器人列表
        """
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                sql = f"select bot_id, prompt, namespace_id, name, memory_limit_size, " \
                      f"welcome_tip, vector_top_k, chains_chunk_type, prompt_variables, " \
                      f"prefix_prompt, prefix_prompt_variables, bot_type, slave_bot_mark," \
                      f"fixed_ques, use_type, suffix_prompt, " \
                      f"id, deleted, creator, create_time, updator, update_time, version, traceability, " \
                      f"origin_domain, fragmented_relationship, slave_carrying_question, " \
                      f"llms, llms_base, suffix_prompt_variables, prompt_ability, bot_role , llms_models " \
                      f"from {self.table_name} where deleted = 0"
                if id:
                    sql = sql + f" and id = '{id}'"
                if bot_id:
                    sql = sql + f" and bot_id = '{bot_id}'"

                cursor.execute(sql)
                data_list = cursor.fetchall()
                logger.info("Request_id={}, [{}]查询结果：{}.", self.request_id, self.table_name, data_list)

                result_list = []
                for data in data_list:
                    result_list.append(ChatBotModel(data))
                return result_list
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
        finally:
            conn.close()

    def find_one(
            self,
            bot_id: str
    ) -> ChatBotModel:
        """
        根据标识查询机器人配置信息
        :param bot_id: 机器人标识
        :return: 机器人Model
        """
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                sql = f"select bot_id, prompt, namespace_id, name, memory_limit_size, " \
                      f"welcome_tip, vector_top_k, chains_chunk_type, prompt_variables, " \
                      f"prefix_prompt, prefix_prompt_variables, bot_type, slave_bot_mark," \
                      f"fixed_ques, use_type, suffix_prompt, " \
                      f"id, deleted, creator, create_time, updator, update_time, version,traceability, " \
                      f"origin_domain, fragmented_relationship, slave_carrying_question, "\
                      f"llms, llms_base, suffix_prompt_variables, prompt_ability, bot_role , llms_models " \
                      f"from {self.table_name} where bot_id = '{bot_id}'"
                cursor.execute(sql)
                data = cursor.fetchone()
                logger.info("Request_id={}, [{}]查询结果：{}.", self.request_id, self.table_name, data)
                if data:
                    return ChatBotModel(data)
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
        finally:
            conn.close()

    def create(
            self,
            bot_id: str,
            name: str,
            welcome_tip: str,
            prompt: str,
            prompt_variables: str,
            prefix_prompt: str = '',
            prefix_prompt_variables: str = '',
            suffix_prompt: str = '',
            namespace_id: str = "0",
            memory_limit_size: int = MEMORY_LIMIT_SIZE,
            vector_top_k: int = VECTOR_SEARCH_TOP_K,
            chains_chunk_type: str = SPLIT_CHUNK_TYPE,
            bot_type: str = "Master",
            slave_bot_mark: str = '',
            fixed_ques: str = '',
            use_type: int = 1
    ) -> int:
        """
        新增机器人
        :param bot_id: 机器人标识
        :param prompt: 提示词信息
        :param prompt_variables: 提示词变量
        :param prefix_prompt: 提示词前缀信息
        :param prefix_prompt_variables: 提示词前缀变量
        :param suffix_prompt: 提示词后缀信息
        :param namespace_id: 知识库标识
        :param name: 机器人名称
        :param memory_limit_size: 长程记忆长度
        :param welcome_tip: 机器人欢迎语
        :param vector_top_k: 语义搜索Top值
        :param chains_chunk_type: 问答链交互类型
        :param bot_type: 机器人类型
        :param slave_bot_mark: 从节点机器人标记
        :param fixed_ques: (Slave类型机器人)固定问题
        :param use_type: 机器人使用类型
        :return: 自增长序号
        """
        conn = get_db_conn()
        try:
            with (conn.cursor() as cursor):
                current_time = datetime.now()
                sql = f"insert into {self.table_name} " \
                      f"(deleted, " \
                      f"creator, " \
                      f"create_time, " \
                      f"updator, " \
                      f"update_time, " \
                      f"version, " \
                      f"bot_id, " \
                      f"prompt, " \
                      f"prompt_variables, " \
                      f"prefix_prompt, " \
                      f"prefix_prompt_variables, " \
                      f"suffix_prompt, " \
                      f"suffix_prompt_variables, " \
                      f"prompt_ability, " \
                      f"namespace_id, " \
                      f"name, " \
                      f"memory_limit_size, " \
                      f"welcome_tip, " \
                      f"vector_top_k, " \
                      f"chains_chunk_type, " \
                      f"bot_type, " \
                      f"slave_bot_mark, " \
                      f"fixed_ques, " \
                      f"use_type) " \
                      f"values ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s'," \
                      f"'%s','%s','%s','%s','%s','%s','%s','%s');" % \
                      ('0', 'system', current_time, 'system', current_time, '0',
                       bot_id, prompt, prompt_variables, prefix_prompt, prefix_prompt_variables, suffix_prompt,
                       namespace_id, name, memory_limit_size, welcome_tip, vector_top_k,
                       chains_chunk_type, bot_type, slave_bot_mark, fixed_ques, use_type)

                cursor.execute(sql.encode('utf-8'))
                conn.commit()
                logger.info("Request_id={}, [{}]保存成功!", self.request_id, self.table_name)
                return cursor.lastrowid
        except Exception as e:
            logger.error("Request_id={}, [{}]数据库操作异常, Message={}", self.request_id, self.table_name, e)
            return 0
        finally:
            conn.close()
