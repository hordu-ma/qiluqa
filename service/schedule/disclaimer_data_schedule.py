import datetime
import random
import uuid
from loguru import logger
from framework.redis.redis_client import RedisClient
from service.domain.ai_disclaimer import DisclaimerModel, AiDisclaimerDomain
from config.base_config import DEFAULT_HAVE_TRACE, DEFAULT_NOT_TRACE
from service.domain.ai_namespace import NamespaceModel

disclaimer_redis_key = 'disclaimer:ai_disclaimer'


def init_disclaimer_data():
    """
    定时任务-初始化免责信息表
    如果redis存在表'disclaimer:ai_disclaimer'则删除表
    重新从Mysql数据库再读出数据并保存到redis数据库中
    """
    try:
        redis_client = RedisClient()
        request_id = str(uuid.uuid4())
        logger.info("###Reload_disclaimer_data###: request_id={} time={}.", request_id, datetime.datetime.now())
        if redis_client.exists(disclaimer_redis_key):
            redis_client.del_key(disclaimer_redis_key)
            redis_set_disclaimer_data(disclaimer_redis_key)
        else:
            redis_set_disclaimer_data(disclaimer_redis_key)
    except Exception as e:
        logger.warning(e)


def reload_disclaimer_data(request_id: str) -> list[DisclaimerModel]:
    val_dict = AiDisclaimerDomain(request_id=request_id).find_all()
    return val_dict


def get_disclaimer_data():
    try:
        redis_client = RedisClient()
        request_id = str(uuid.uuid4())
        logger.info("###Reload_disclaimer_data###: request_id={} time={}.", request_id, datetime.datetime.now())
        val_dict = redis_client.get_hash(disclaimer_redis_key)
        disclaimer_data = []
        for data in val_dict.values():
            data = eval(data)
            # disclaimer不空且没被删除
            if data is not None and data['deleted'] == 0:
                if data['text'] and data['random_weight']:
                    disclaimer_data.append(data)
        return disclaimer_data
    except Exception as e:
        logger.error(e)
        return {}


def redis_set_disclaimer_data(pkey: str):
    redis_client = RedisClient()
    request_id = str(uuid.uuid4())
    data_list = reload_disclaimer_data(request_id=request_id)
    if data_list:
        for data in data_list:
            try:
                redis_client.set_hash_by_key(pkey, key=data.id,
                                             v=str(data.default_serializer()))
            except Exception as err:
                logger.warning(err)
                logger.log("####redis_set_disclaimer_data INFO，request_id={}, key={}.", request_id, pkey)


def sort_disclaimer_data(namespaceModel: NamespaceModel):
    disclaimer_has_trace_text = []
    disclaimer_not_trace_text = []
    disclaimer_has_trace_weight = []
    disclaimer_not_trace_weight = []
    disclaimer_result = get_disclaimer_data()
    logger.info("###get_disclaimer_text INFO, disclaimer_result.length={}.", len(disclaimer_result))
    for disclaimer_data in disclaimer_result:
        logger.info("###get_disclaimer_text INFO, disclaimer_data.has_trace_flag={}, disclaimer_data.namespace_id={}, namespaceModel.id={}.",
                    disclaimer_data['has_trace_flag'], disclaimer_data['namespace_id'], namespaceModel.id)
        if str(disclaimer_data['namespace_id']) == str(namespaceModel.id):
            if disclaimer_data['has_trace_flag'] == '1':
                disclaimer_has_trace_text.append(disclaimer_data['text'])
                disclaimer_has_trace_weight.append(float(disclaimer_data['random_weight']))
            elif disclaimer_data['has_trace_flag'] == '0':
                disclaimer_not_trace_text.append(disclaimer_data['text'])
                disclaimer_not_trace_weight.append(float(disclaimer_data['random_weight']))
    logger.info(
        "###get_disclaimer_text INFO, disclaimer_has_trace_text.length={}, disclaimer_not_trace_text.length={}.",
        len(disclaimer_has_trace_text), len(disclaimer_not_trace_text))
    if not disclaimer_has_trace_text or not disclaimer_not_trace_text:
        return DEFAULT_HAVE_TRACE, DEFAULT_NOT_TRACE
    has_trace_text = random.choices(disclaimer_has_trace_text, disclaimer_has_trace_weight, k=1)
    not_trace_text = random.choices(disclaimer_not_trace_text, disclaimer_not_trace_weight, k=1)
    return has_trace_text[0], not_trace_text[0]