import datetime
import traceback
import uuid
from loguru import logger

from service.domain.ai_namespace import AiNamespaceDomain
from framework.business_code import ERROR_10001, ERROR_10213
from framework.business_except import BusinessException
from service.domain.ai_namespace_file import NamespaceFileModel, AiNamespaceFileDomain
from service.local_repo_service import LocalRepositoryDomain


def handle(
        namespaceFileModel: NamespaceFileModel,
        namespaceFileDomain: AiNamespaceFileDomain,
        request_id: str = str(uuid.uuid4()),
):
    """
    业务处理
    :param namespaceFileModel:  知识库文件实体对象
    :param namespaceFileDomain: 知识库文件服务
    :param request_id: 请求唯一标识
    """
    try:
        # 对于向量化成功文件更改分片策略
        # 知识文件是否可以生成分片
        if not namespaceFileModel.is_want_generate_chunk():
            logger.error("###Reload_namespace_file handle ERROR, [{}]知识库文件[{}]的向量化状态异常，不可执行向量化操作, "
                         "request_id={}.", ERROR_10213, namespaceFileModel.id, request_id)
            raise BusinessException(ERROR_10213.code, ERROR_10213.message)

        # 查询文件所属知识库信息
        namespace_id = namespaceFileModel.namespace_id
        namespaceModel = AiNamespaceDomain(request_id=request_id).find_by_id(namespace_id)
        if not namespaceModel:
            logger.error("###Reload_namespace_file handle ERROR, [{}]未查询到所属知识库[{}]信息, request_id={}.", ERROR_10001, namespace_id, request_id)
            raise BusinessException(ERROR_10001.code, ERROR_10001.message)

        vector_count = int(namespaceFileModel.vector_count)
        # 更新向量状态，Vectoring
        namespaceFileDomain.update(
            file_id=namespaceFileModel.id,
            vector_ids=[],
            vector_status='Vectoring',
            vector_count=vector_count
        )
        # 向本地知识库推送元数据
        ids = LocalRepositoryDomain(request_id=request_id).push(
            glob=namespaceFileModel.name,
            namespaceModel=namespaceModel,
            namespaceFileModel=namespaceFileModel,
        )
        # 成功场景: 同步更新至业务库-知识库表
        namespaceFileDomain.update(
            file_id=namespaceFileModel.id,
            vector_ids=ids,
            vector_status='Done',
            vector_count=vector_count
        )
        logger.info("###Reload_namespace_file###向量化文件成功：文件名称[{}], 向量标识[{}].", namespaceFileModel.name, ids)
    except Exception as err:
        logger.error("###Reload_namespace_file###向量化文件失败：文件名称[{}], Message={}.", namespaceFileModel.name, err)
        traceback.print_exc()
        # 失败场景: 同步更新至业务库-知识库表
        vector_count = int(namespaceFileModel.vector_count)+1
        namespaceFileDomain.update(
            file_id=namespaceFileModel.id,
            vector_ids=[],
            vector_status='Fail',
            vector_count=vector_count
        )
