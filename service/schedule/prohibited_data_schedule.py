import datetime
import uuid
from framework.redis.redis_client import RedisClient
from loguru import logger
from service.domain.ai_prohibited import AiProhibitedDomain,ProhibitedModel

prohibited_redis_key = 'prohibited:ai_prohibited'


def init_prohibited_data():
    """
    定时任务-初始化敏感禁用词
    如果redis存在表'prohibited:ai_prohibited'则删除表
    重新从Mysql数据库再读出数据并保存到redis数据库中
    """
    try:
        redis_client = RedisClient()
        request_id = str(uuid.uuid4())
        logger.info("###Reload_prohibited_data###: request_id={} time={}.", request_id, datetime.datetime.now())
        if redis_client.exists(prohibited_redis_key):
            redis_client.del_key(prohibited_redis_key)
            redis_set_prohibited_data(prohibited_redis_key)
        else:
            redis_set_prohibited_data(prohibited_redis_key)
    except Exception as e:
        logger.warning(e)


def redis_set_prohibited_data(pkey: str):
    redis_client = RedisClient()
    request_id = str(uuid.uuid4())
    data_list = reload_prohibited_data(request_id=request_id)
    if data_list:
        for data in data_list:
            try:
                redis_client.set_hash_by_key(pkey, key=data.id,
                                             v=str(data.default_serializer()))
            except Exception as err:
                logger.warning(err)
                logger.info("####redis_set_prohibited_data fail，request_id={}, key={}.", request_id, pkey)


def reload_prohibited_data(request_id: str) -> list[ProhibitedModel]:
    val_dict = AiProhibitedDomain(request_id=request_id).find_all()
    return val_dict


def get_prohibited_data():
    try:
        redis_client = RedisClient()
        request_id = str(uuid.uuid4())
        logger.info("###Reload_prohibited_data###: request_id={} time={}.", request_id, datetime.datetime.now())
        val_dict = redis_client.get_hash(prohibited_redis_key)
        return val_dict
    except Exception as e:
        logger.error(e)
        logger.info("####get_prohibited_data fail.")
        return {}

