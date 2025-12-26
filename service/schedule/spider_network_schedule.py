import datetime
import time
import uuid
from loguru import logger
from service.domain.ai_namespace_file import AiNamespaceFileDomain
from service.domain.ai_namespace_network import AiNamespaceNetworkDomain
from service.namespacefile.namespace_file_service import NamespaceFileService


def get_network_data():
    request_id = str(uuid.uuid4())
    logger.info("###Reload_namespace_file###: request_id={} time={}.", request_id, datetime.datetime.now())
    list_namespaceNetworkDomain = AiNamespaceNetworkDomain(request_id=request_id).find_all_update_network()
    return list_namespaceNetworkDomain


def rewrite_spider_network():
    """
    定时任务-本地知识库文件向量化处理
    """
    try:
        request_id = str(uuid.uuid4())
        current_timestamp = int(time.time() * 1000)
        logger.info("###Rewrite_spider_network###: request_id={} time={}.", request_id, datetime.datetime.now())
        network_data = get_network_data()
        if network_data:
            for data in network_data:
                if int(data.next_time) <= current_timestamp:
                    network_model = AiNamespaceNetworkDomain(request_id=request_id).find_by_url_id(data.id)
                    namespaceFileModel = AiNamespaceFileDomain(request_id=request_id).find_by_id(data.file_id)
                    # 更新网页爬取信息数据
                    NamespaceFileService(request_id=request_id).update_spider_url_info(
                        network_model=network_model,
                        url=data.website,
                        filename=namespaceFileModel.name,
                        path=namespaceFileModel.path
                    )
                    # 更新下次爬虫时间
                    AiNamespaceNetworkDomain(request_id=request_id).update_next_time(
                        network_model=network_model
                    )
        else:
            logger.info("###Rewrite_spider_network###: No network data to process.")
    except Exception as e:
        logger.error("###Rewrite_spider_network###: Exception occurred{}.", str(e))
