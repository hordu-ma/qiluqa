import traceback
import uuid
from fastapi import APIRouter, Body
from loguru import logger
from fastapi import (File, UploadFile)
from config.base_config import CONTENT_PATH
from custom.bespin.aigc import QwenVL
from custom.bespin.document.document_loader import CusDocumentLoader
from custom.bespin.graphs.graph_neo4j_service import GraphNeo4jService
from custom.bespin.graphs.neo4j_request import ChatParam, ChatParamExamples
from custom.bespin.graphs.neo4j_response import ChatResponse, ChatResponseExamples
from framework.api_model import QueryResponse
from framework.business_except import BusinessException


router = APIRouter()


@router.post(
    path="/bespin/graphs/call-neo4j",
    tags=["Bespin:贝斯平定制模块"],
    summary="知识图谱检索功能",
    response_model=ChatResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
    responses=ChatResponseExamples.examples
)
def api_bsp_call_neo4j(
        data: ChatParam = Body(
            default=...,
            examples=ChatParamExamples.examples
        ),
) -> QueryResponse:
    """
    知识图谱检索功能
    :param data: 业务参数\n
    :return: 检索结果\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    logger.info("###API###api_bsp_call_neo4j info, request_id={}, data={}.", request_id, data)
    try:
        response.data = GraphNeo4jService(
            is_direct_return=data.is_direct_return,
            is_middle_return=data.is_middle_return,
        ).call(ques=data.ques)
    except BusinessException as business_err:
        logger.error("###API###api_bsp_call_neo4j error, request_id={}, err={}.", request_id, business_err)
        traceback.print_exc()
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_bsp_call_neo4j error, request_id={}, err={}.", request_id, err)
        traceback.print_exc()
        response.message = str(err)
        response.status = -1
    return response


@router.post(
    path="/bespin/document/loader",
    tags=["Bespin:贝斯平定制模块"],
    summary="文档加载服务",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
async def api_bsp_document_loader(
        base_file: UploadFile = File(...)
) -> QueryResponse:
    """
    文档加载服务\n
    :param base_file: 素材文档\n
    :return: QueryResponse\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        # 文档保存临时目录
        filepath = CONTENT_PATH + base_file.filename
        content = await base_file.read()
        with open(filepath, 'wb') as f:
            f.write(content)
        # 临时目录解析文档
        response.data = CusDocumentLoader(request_id=request_id).loader(
            document_glob=base_file.filename,
            document_path=CONTENT_PATH
        )
    except BusinessException as business_err:
        logger.error("###API###api_bsp_document_loader error, request_id={}, err={}.", request_id, business_err)
        traceback.print_exc()
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_bsp_document_loader error, request_id={}, err={}.", request_id, err)
        traceback.print_exc()
        response.message = str(err)
        response.status = -1
    return response


@router.post(
    path="/bespin/aigc/qwen-vl",
    tags=["Bespin:贝斯平定制模块"],
    summary="开源视觉理解大模型服务",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
def api_bsp_aigc_qwen_vl(
        ques: str,
        image: str
) -> QueryResponse:
    """
    开源视觉理解大模型服务\n
    :param ques: 问题\n
    :param image: 图片\n
    :return: QueryResponse\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        response.data = QwenVL().call(ques=ques, image=image)
    except BusinessException as business_err:
        logger.error("###API###api_bsp_aigc_qwen_vl error, request_id={}, err={}.", request_id, business_err)
        traceback.print_exc()
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_bsp_aigc_qwen_vl error, request_id={}, err={}.", request_id, err)
        traceback.print_exc()
        response.message = str(err)
        response.status = -1
    return response
