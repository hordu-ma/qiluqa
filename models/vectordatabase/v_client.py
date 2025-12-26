from loguru import logger

from config.base_config import VECTOR_DATABASE_TYPE
from framework.business_except import BusinessException
from models.vectordatabase.base_vector_client import BaseVectorClient
from models.vectordatabase.vector_postgres_client import VectorPostgresClient


def get_instance_client() -> BaseVectorClient:
    """
    获取向量库客户端实例对象
    :return: 实例对象
    """
    try:
        if VECTOR_DATABASE_TYPE == 'Postgres':
            return VectorPostgresClient()
        else:
            pass
    except Exception as err:
        logger.error("######[10200]VectorClient model[{}] invoke error: {}", VECTOR_DATABASE_TYPE, err)
        raise BusinessException(10200, "向量库客户端初始化失败！")


    