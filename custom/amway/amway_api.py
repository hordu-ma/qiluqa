# -*- coding: utf-8 -*-
import traceback
import uuid
from typing import List, Tuple
from fastapi import (File, UploadFile, Body, APIRouter)
from loguru import logger
from custom.amway.aigc.face_chain_client import FaceChainClient
from custom.amway.aigc.infer_param import InferParam, FcInferParam
from custom.amway.aigc.service.aigc_service import AmwayAIGC
from custom.amway.aigc.train_param import TrainParam, FcTrainParam
from custom.amway.allm.baidubce.baidubce_client import BaidubceClient
from custom.amway.amway_config import SFT_SOURCE_PATH, SFT_TARGET_PATH
from custom.amway.cvision.service.cvision_service import CvDomain
from custom.amway.prepare.service.prepare_update_param import PrepareUpdateParam
from custom.amway.sft.service.sft_data_service import SftDataService
from custom.amway.speech.service.speech_service import SpeechText
from framework.business_except import BusinessException
from custom.amway.prepare.service.prepare_services import NamespacePrepare, NamespacePrepareService
from config.base_config import *
from framework.api_model import QueryResponse


router = APIRouter()


@router.post(
    path="/amway/prepare/upload",
    tags=["Amway:安利定制模块"],
    summary="知识库上传预制文件",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
async def api_prepare_upload(
        user_file: UploadFile = File(...),
        namespace_id: str = None,
        encoding: str = 'gb18030',
) -> QueryResponse:
    """
    知识库上传预制文件\n
    :param user_file: 预制文件路径\n
    :param namespace_id: 知识库标识\n
    :param encoding: 编码\n
    :return: QueryResponse\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        # 上传文件保存至临时目录
        file_path = CONTENT_PATH + user_file.filename
        content = await user_file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        # 开始获取
        namespacePrepare = NamespacePrepare(
            path=CONTENT_PATH,
            file_type=user_file.content_type,
            file_path=file_path,
            file_name=user_file.filename,
            file_size=user_file.size,
            namespace_id=namespace_id,
            encoding=encoding,
            request_id=request_id,
        )
        namespacePrepare.transformer()
    except BusinessException as business_err:
        logger.error("###API###api_prepare_upload error, requestId={}, err={}.", request_id, business_err)
        traceback.print_exc()
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_prepare_upload error, requestId={}, err={}.", request_id, err)
        traceback.print_exc()
        response.message = str(err)
        response.status = -1
    return response


@router.post(
    path="/amway/prepare/insert",
    tags=["Amway:安利定制模块"],
    summary="知识库添加预制数据",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
async def api_prepare_insert(
        namespace_id: str,
        data_list: List[Tuple],
        remark: str = None,
) -> QueryResponse:
    """
    知识库添加预制数据\n
    :param namespace_id: 知识库标识\n
    :param data_list: 编码\n
    :param remark: 备注信息\n
    :return: QueryResponse\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        # 开始获取
        namespacePrepare = NamespacePrepare(
            path=CONTENT_PATH,
            file_type="",
            file_path="",
            file_name="",
            file_size=0,
            namespace_id=namespace_id,
            scene="insert",
            data_list=data_list,
            remark=remark,
            request_id=request_id,
        )
        namespacePrepare.transformer()
    except BusinessException as business_err:
        logger.error("###API###api_prepare_insert error, requestId={}, err={}.", request_id, business_err)
        traceback.print_exc()
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_prepare_insert error, requestId={}, err={}.", request_id, err)
        traceback.print_exc()
        response.message = str(err)
        response.status = -1
    return response


@router.post(
    path="/amway/prepare/update",
    tags=["Amway:安利定制模块"],
    summary="知识库修改预制数据",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
async def api_prepare_update(
        namespace_id: str,
        file_id: str = None,
        file_name: str = "",
        file_path: str = "",
        file_type: str = "",
        file_size: str = "0",
        file_display_name: str = "",
        remark: str = None,
        data: PrepareUpdateParam = Body(...),
) -> QueryResponse:
    """
    知识库修改预制数据\n
    :param namespace_id: 知识库标识\n
    :param file_id: 文件标识\n
    :param file_name: 文件名称\n
    :param file_path: 文件路径\n
    :param file_type: 文件类型\n
    :param file_size: 文件大小\n
    :param file_size: 文件大小\n
    :param file_display_name: 文件显示名称\n
    :param remark: 备注信息\n
    :param data: 数据\n
    :return: QueryResponse\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        namespacePrepareService = NamespacePrepareService(
            namespace_id=namespace_id,
            name=file_name,
            path=file_path,
            type=file_type,
            size=file_size,
            file_id=file_id,
            file_display_name=file_display_name,
            remark=remark,
            param=data,
            request_id=request_id,
        )
        namespacePrepareService.handle()
    except BusinessException as business_err:
        logger.error("###API###api_prepare_update error, requestId={}, err={}.", request_id, business_err)
        traceback.print_exc()
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_prepare_update error, requestId={}, err={}.", request_id, err)
        traceback.print_exc()
        response.message = str(err)
        response.status = -1
    return response


@router.post(
    path="/amway/aigc/train",
    tags=["Amway:安利定制模块"],
    summary="AIGC训练",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
def api_aigc_train(
        data: TrainParam = Body(...),
) -> QueryResponse:
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        aigc = AmwayAIGC(request_id=request_id)
        aigc.train(param=data)
    except BusinessException as business_err:
        logger.error("###API###api_aigc_train error, requestId={}, err={}.", request_id, business_err)
        traceback.print_exc()
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_aigc_train error, requestId={}, err={}.", request_id, err)
        traceback.print_exc()
        response.message = str(err)
        response.status = -1
    return response


@router.post(
    path="/amway/aigc/infer",
    tags=["Amway:安利定制模块"],
    summary="AIGC推理",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
def api_aigc_infer(
        data: InferParam = Body(...),
) -> QueryResponse:
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        aigc = AmwayAIGC(request_id=request_id)
        response.data = {
            "target": aigc.infer(param=data)
        }
    except BusinessException as business_err:
        logger.error("###API###api_aigc_infer error, requestId={}, err={}.", request_id, business_err)
        traceback.print_exc()
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_aigc_infer error, requestId={}, err={}.", request_id, err)
        traceback.print_exc()
        response.message = str(err)
        response.status = -1
    return response


@router.post(
    path="/amway/aigc/fc/train",
    tags=["Amway:安利定制模块"],
    summary="AIGC-FC 训练",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
async def api_aigc_fc_train(
        data: FcTrainParam = Body(...),
) -> QueryResponse:
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        client = FaceChainClient()
        response.data = client.train(
            img64_list=data.img64_list,
            person_name=data.person_name,
        )
    except BusinessException as business_err:
        logger.error("###API###api_aigc_fc_train error, requestId={}, err={}.", request_id, business_err)
        traceback.print_exc()
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_aigc_fc_train error, requestId={}, err={}.", request_id, err)
        traceback.print_exc()
        response.message = str(err)
        response.status = -1
    return response


@router.post(
    path="/amway/aigc/fc/infer",
    tags=["Amway:安利定制模块"],
    summary="AIGC-FC 推理",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
async def api_aigc_fc_infer(
        data: FcInferParam = Body(...),
) -> QueryResponse:
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        client = FaceChainClient()
        response.data = client.infer(
            style=data.style,
            person_name=data.person_name,
            num_generate=data.num_generate,
        )
    except BusinessException as business_err:
        logger.error("###API###api_aigc_fc_infer error, requestId={}, err={}.", request_id, business_err)
        traceback.print_exc()
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_aigc_fc_infer error, requestId={}, err={}.", request_id, err)
        traceback.print_exc()
        response.message = str(err)
        response.status = -1
    return response


@router.post(
    path="/amway/aigc/zh/init-aigc",
    tags=["Amway:安利定制模块"],
    summary="作画功能",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
def api_zh_init_aigc(
        text: str,
        resolution: str,
        style: str,
        num: int = 1
) -> QueryResponse:
    """
    作画功能\n
    :param text: 输入内容，长度不超过100个字\n
    :param resolution: 图片分辨率，可支持1024*1024、1024*1536、1536*1024\n
    :param style: 目前支持风格有：探索无限、古风、二次元、写实风格、浮世绘、low poly 、未来主义、像素风格、概念艺术、赛博朋克、洛丽塔风格、巴洛克风格、超现实主义、水彩画、蒸汽波艺术、油画、卡通画\n
    :param num: 图片生成数量，支持1-6张\n
    :return: 业务数据\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        response.data = BaidubceClient(request_id=request_id).init_aigc(
            text=text,
            resolution=resolution,
            style=style,
            num=num
        )
    except BusinessException as business_err:
        logger.error("###API###api_zh_init_aigc error, requestId={}, err={}.", request_id, business_err)
        traceback.print_exc()
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_zh_init_aigc error, requestId={}, err={}.", request_id, err)
        traceback.print_exc()
        response.message = str(err)
        response.status = -1
    return response


@router.post(
    path="/amway/aigc/zh/get-aigc",
    tags=["Amway:安利定制模块"],
    summary="查询作画功能",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
def api_zh_get_aigc(
        taskId: str
) -> QueryResponse:
    """
    查询作画功能\n
    :param taskId: 图片生成任务ID\n
    :return: 业务数据\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        response.data = BaidubceClient(request_id=request_id).get_aigc(taskId=taskId)
    except BusinessException as business_err:
        logger.error("###API###api_zh_get_aigc error, requestId={}, err={}.", request_id, business_err)
        traceback.print_exc()
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_zh_get_aigc error, requestId={}, err={}.", request_id, err)
        traceback.print_exc()
        response.message = str(err)
        response.status = -1
    return response


@router.post(
    path="/sft/init-data",
    tags=["Amway:安利定制模块"],
    summary="初始化生成SFT数据",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
def api_init_sft_data(
        source_file_path: str = None,
        target_file_path: str = None,
) -> QueryResponse:
    """
    初始化生成SFT数据\n
    :param source_file_path: 需要微调的源文件目录\n
    :param target_file_path: 指定微调数据的存放目录\n
    :return: QueryResponse\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        if not source_file_path:
            source_file_path = SFT_SOURCE_PATH
        if not target_file_path:
            target_file_path = SFT_TARGET_PATH
        service = SftDataService(
            source_file_path=source_file_path,
            target_file_path=target_file_path,
        )
        service.transform()
        logger.info("#########api_init_sft_data success! request_id={}", request_id)
    except BusinessException as business_err:
        logger.error("###API###api_init_sft_data error, requestId={}, err={}.", request_id, business_err)
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_init_sft_data error, requestId={}, err={}.", request_id, err)
        response.message = str(err)
        response.status = -1
    return response


@router.post(
    path="/sft/loader",
    tags=["Amway:安利定制模块"],
    summary="加载分析源文本数据",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
def api_load_sft_data(
        source_file_path: str = None,
        target_file_path: str = None,
) -> QueryResponse:
    """
    加载分析源文本数据\n
    :param source_file_path: 需要微调的源文件目录\n
    :param target_file_path: 指定微调数据的存放目录\n
    :return: QueryResponse\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        if not source_file_path:
            source_file_path = SFT_SOURCE_PATH
        if not target_file_path:
            target_file_path = SFT_TARGET_PATH
        service = SftDataService(
            source_file_path=source_file_path,
            target_file_path=target_file_path,
        )
        docs = service.reload()
        metadata = [doc.metadata for doc in docs]
        response.data = {
            "total": len(metadata),
            "metadata": metadata
        }
        logger.info("#########api_load_sft_data success! request_id={}, 文件总数=[{}], 元数据=[{}].",
                    request_id, len(metadata), metadata)
    except BusinessException as business_err:
        logger.error("###API###api_load_sft_data error, requestId={}, err={}.", request_id, business_err)
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_load_sft_data error, requestId={}, err={}.", request_id, err)
        response.message = str(err)
        response.status = -1
    return response


@router.post(
    path="/chat/ask-cv",
    tags=["Amway:安利定制模块"],
    summary="简历问答接口",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
def api_chat_ask_cv(
        ques: str,
        bot_id: str,
        num: int,
        user_id: str = None,
        namespace_id: str = None,
) -> QueryResponse:
    """
    简历问答接口\n
    :param ques: 问题\n
    :param bot_id: 机器人标识\n
    :param num: 筛选份数\n
    :param user_id: 用户标识\n
    :param namespace_id: 指定知识库标识\n
    :return: QueryResponse\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        # 简历问答
        response.data = CvDomain(request_id=request_id).ask(
            ques=ques,
            bot_id=bot_id,
            num=num,
            user_id=user_id,
            namespace_id=namespace_id,
            request_id=request_id
        )
    except BusinessException as business_err:
        logger.error("###API###api_chat_ask_cv error, requestId={}, err={}.", request_id, business_err)
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_chat_ask_cv error, requestId={}, err={}.", request_id, err)
        traceback.print_exc()
        response.message = str(err)
        response.status = -1
    return response


@router.post(
    path="/generate/speech",
    tags=["Amway:安利定制模块"],
    summary="生成演讲稿",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
def api_generate_speech(
        ques: str,
        bot_id: str,
        namespace_id_business: str,
        namespace_id_style: str,
        user_id: str = None,
) -> QueryResponse:
    """
    生成演讲稿接口\n
    :param ques: 问题\n
    :param bot_id: 机器人标识\n
    :param user_id: 用户标识\n
    :param namespace_id_business: 业务背景知识库标识\n
    :param namespace_id_style: 风格背景知识库标识\n
    :return: QueryResponse\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        speechText = SpeechText(
            ques=ques,
            bot_id=bot_id,
            user_id=user_id,
            namespace_id_business=namespace_id_business,
            namespace_id_style=namespace_id_style,
            request_id=request_id,
        )
        response.data = speechText.transform()
    except BusinessException as business_err:
        logger.error("###API###api_generate_speech error, requestId={}, err={}.", request_id, business_err)
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_generate_speech error, requestId={}, err={}.", request_id, err)
        response.message = str(err)
        response.status = -1
    return response
