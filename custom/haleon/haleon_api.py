# -*- coding: utf-8 -*-
import traceback
import uuid
from fastapi import APIRouter, Body, UploadFile, File
from loguru import logger
from config.base_config import CONTENT_PATH
from custom.haleon.param.chat_param import ChatParam, ChatParamExamples
from framework.api_model import QueryResponse
from framework.business_except import BusinessException
from service.chat_private_service import ChatPrivateDomain
from service.chat_response import ChatResponse, ChatResponseExamples


router = APIRouter()


@router.post(
    path="/haleon/chat/private/ask",
    tags=["Haleon:赫力昂定制模块"],
    summary="赫力昂专用领域问答接口",
    response_model=ChatResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
    responses=ChatResponseExamples.examples
)
def api_hn_chat_ask(
        data: ChatParam = Body(
            default=...,
            examples=ChatParamExamples.examples
        ),
) -> QueryResponse:
    """
    赫力昂专用领域问答接口\n
    :param data: 业务参数\n
    :return: 问答结果\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    logger.info("###API###api_hn_chat_ask info, request_id={}, data={}", request_id, data)
    try:
        return ChatPrivateDomain(request_id).ask(
            ques=data.ques,
            bot_id=data.bot_id,
            user_id=data.user_id,
            group_uuid=data.group_uuid,
            answer_type=data.answer_type,
            crowd_type=data.crowd_type,
            use_mark=",".join(data.use_mark) if data.use_mark else None,
            scene=data.scene,
        )
    except BusinessException as business_err:
        logger.error("###API###api_hn_chat_ask error, requestId={}, err={}.", request_id, business_err)
        traceback.print_exc()
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_hn_chat_ask error, requestId={}, err={}.", request_id, err)
        traceback.print_exc()
        response.message = str(err)
        response.status = -1
    return response


