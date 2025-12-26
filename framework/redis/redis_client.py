import redis
from typing import Any
from loguru import logger
from config.base_config import *


class RedisClient:
    """
    Redis客户端工具类

    Example:
        .. code-block:: python
            from redis_client import RedisClient

            client = RedisClient(
                host='127.0.0.1',
                port='6379',
                password='abc',
            )
        .. code-block:: bash
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        构造方法-单例模式
        :param args:
        :param kwargs:
        """
        if not cls._instance:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(
            self,
            host: str = REDIS_HOST,
            port: str = REDIS_PORT,
            password: str = REDIS_PASSWD,
            db: str = REDIS_DATABASE,
            decode_responses: bool = True,
            min_connections: str = REDIS_MIN,
            max_connections: str = REDIS_MAX,
    ):
        """
        构造方法-设置成员变量-初始化连接池
        :param host: 主机
        :param port: 端口
        :param password: 密码
        :param db: 数据库
        :param decode_responses: 返回结果是否转为字符串
        :param max_connections: 最大连接数
        """
        if not hasattr(self, 'pool'):
            try:
                logger.info("###Redis_Client INFO, 开始初始化连接池信息, host={}, port={}, password={}, db={}, "
                            "decode_responses={}, max_connections={}.", host, port, password, db, decode_responses, max_connections)
                if password:
                    self.pool = redis.ConnectionPool(
                        host=host,
                        port=port,
                        password=password,
                        db=db,
                        decode_responses=decode_responses,
                        max_connections=int(max_connections),
                    )
                else:
                    self.pool = redis.ConnectionPool(
                        host=host,
                        port=port,
                        db=db,
                        decode_responses=decode_responses,
                        max_connections=max_connections,
                    )
                logger.info("###Redis_Client INFO, 连接池初始化成功, Pool={}.", self.pool)
            except Exception as err:
                logger.error("###Redis_Client __init__ error, 初始化获取Redis连接池失败, err={}", err)
                raise err

    def _get_conn(self) -> redis.Redis:
        """
        从连接池中获取一个实例
        :return: redis实例
        """
        try:
            logger.info("###Redis_Client INFO, 开始获取连接对象...")
            _conn = redis.StrictRedis(connection_pool=self.pool)
            logger.info("###Redis_Client INFO, 获取连接对象成功, _conn={}", _conn)
            return _conn
        except Exception as err:
            logger.error("###Redis_Client _get_conn error, 获取Redis实例失败, err={}", err)
            raise err

    def del_key(self, key: str):
        """
        删除指定键的数据
        :param key: 键
        :return: None
        """
        return self._get_conn().delete(key)

    def exists(self, key: str) -> bool:
        """
        识别指定键是否存在
        :param key: 键
        :return: bool
        """
        return bool(self._get_conn().exists(key))

    def get_str(self, key: str):
        """
        读取-字符串
        :param key: 键
        :return: 值
        """
        return self._get_conn().get(name=key)

    def set_str(self, key: str, val: str):
        """
        添加-字符串
        :param key: 键
        :param val: 值
        :return: None
        """
        self._get_conn().set(name=key, value=val)

    def set_str_time(self, key: str, val: str, time: int):
        """
        添加-字符串并设置过期时间
        :param key: 键
        :param val: 值
        :param time: 过期时间，单位秒
        :return: None
        """
        self._get_conn().set(name=key, value=val, ex=time)

    def push_list_l(self, key: str, value: Any):
        """
        列表 - 从左侧进
        :param key: 键
        :param value: 值
        :return: None
        """
        self._get_conn().lpush(key, value)

    def push_list_r(self, key: str, value: Any):
        """
        列表 - 从右侧进
        :param key: 键
        :param value: 值
        :return: None
        """
        self._get_conn().rpush(key, value)

    def get_list_len(self, key: str):
        """
        列表 - 获取长度信息
        :param key: 键
        :return: 列表长度
        """
        return self._get_conn().llen(key)

    def pop_list_l(self, key: str):
        """
        列表 - 从左侧移除一个元素并返回对应值
        :param key: 键
        :return: 值
        """
        return self._get_conn().lpop(key)

    def pop_list_r(self, key: str):
        """
        列表 - 从右侧移除一个元素并返回对应值
        :param key: 键
        :return: 值
        """
        return self._get_conn().rpop(key)

    def get_list(self, key: str):
        """
        列表 - 获取列表中所有值
        :param key: 键
        :return: 值
        """
        return self._get_conn().lrange(key, 0, -1)

    def set_hash(self, pkey, v):
        self._get_conn().hmset(pkey, v)

    def set_hash_by_key(self, pkey, key, v):
        self._get_conn().hset(pkey, key, v)

    def get_hash_by_key(self, pkey, key):
        return self._get_conn().hget(pkey, key)

    def get_hash(self, pkey):
        return self._get_conn().hgetall(pkey)

    def expire(self, key: str, time: int):
        return self._get_conn().expire(key, time)

# if __name__ == "__main__":
#     _client = RedisClient(
#         host=REDIS_HOST,
#         port=REDIS_PORT,
#         password=REDIS_PASS,
#         db=REDIS_DB_NUM,
#         max_connections=REDIS_MAX_CONN,
#     )
#     print(_client.exists("3"))
