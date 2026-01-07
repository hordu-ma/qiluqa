import json
import time
import traceback
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING

import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from loguru import logger
from sse_starlette.sse import EventSourceResponse
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles

from config.base_config import *
from config.loguru_config import init_log_config
from custom.amway import amway_api

from starlette.responses import StreamingResponse
from custom.bespin import bespin_api
from custom.haleon import haleon_api
from framework.api_model import QueryResponse
from framework.business_code import ERROR_10207
from framework.business_except import BusinessException
from models.vectordatabase.v_client import get_instance_client
from service.bot_service import BotInitDomain
from service.chat_private_service import ChatPrivateDomain
from service.chat_public_service import ChatPublicDomain
from service.domain.ai_chat_bot import AiChatBotDomain
from service.domain.ai_chat_history import AiChatHistoryDomain
from service.domain.ai_namespace import AiNamespaceDomain
from service.domain.ai_namespace_file import AiNamespaceFileDomain
from service.local_repo_service import LocalRepositoryDomain
from service.namespacefile.namespace_file_request import (
    DelChunkParam,
    DelFileParam,
)
from service.schedule.spider_network_schedule import rewrite_spider_network

app = FastAPI(title="BespinGLM模型层-主应用工程")
app.include_router(haleon_api.router)
app.include_router(amway_api.router)
app.include_router(bespin_api.router)
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "framework" / "static" / "swagger-ui"), name="static")
scheduler = BackgroundScheduler()


# @app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """
    Swagger
    :return:
    """
    openapi_url = app.openapi_url
    oauth2_redirect_url = app.swagger_ui_oauth2_redirect_url
    if openapi_url is None or oauth2_redirect_url is None:
        return RedirectResponse(url="/redoc")
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=app.title + " - Swagger UI",
        oauth2_redirect_url="/docs/oauth2-redirect",
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@app.get("/docs/oauth2-redirect", include_in_schema=False)
async def swagger_ui_redirect():
    """
    Swagger
    :return:
    """
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """
    Swagger
    :return:
    """
    openapi_url = app.openapi_url
    if openapi_url is None:
        return RedirectResponse(url="/")
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=app.title + " - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )


@app.on_event("startup")
async def start_scheduler():
    """
    1.日志框架初始化配置\n
    2.定时任务初始化配置\n
    :return:\n
    """
    init_log_config()
    #   init_prohibited_data()
    #   init_disclaimer_data()
    #   if SCHEDULES_PROHIBITED:
    #       scheduler.add_job(init_prohibited_data, 'interval', seconds=SCHEDULES_PROHIBITED_SECONDS)
    #   if SCHEDULES_DISCLAIMER:
    #       scheduler.add_job(init_disclaimer_data, 'interval', seconds=SCHEDULES_DISCLAIMER_SECONDS)
    if SCHEDULES_SPIDER:
        scheduler.add_job(rewrite_spider_network, "interval", seconds=SCHEDULES_SPIDER_SECONDS)
    if SCHEDULES_ENABLED:
        scheduler.start()
    logger.info("Application 启动成功! 执行时间: ", end=" ")
    logger.info(f"{datetime.now():%Y-%m-%d %H:%M:%S}")


@app.on_event("shutdown")
async def stop_scheduler():
    """
    定时任务回收化配置\n
    :return:\n
    """
    if SCHEDULES_ENABLED:
        scheduler.shutdown()


@app.get(path="/", include_in_schema=False)
async def document():
    """
    访问根目录时重定向至文档地址\n
    :return: None\n
    """
    return RedirectResponse(url="/docs")


@app.middleware("http")
async def _aop_info_(request: Request, call_next):
    """
    中间件: 请求日志埋点\n
    :param request: 请求\n
    :param call_next: 回调函数\n
    :return: Response\n
    """
    logger.info("###API###AOP#### Request Header={}, Url={}.", request.headers, request.url)
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info("###API###AOP#### Response Header={}.", response.headers)
    return response


@app.post(
    path="/knowledge-base/upload",
    tags=["KnowledgeBase:知识库模块"],
    summary="知识库上传文件",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
async def api_upload_file(user_file: UploadFile = File(...), namespace_id: str | None = None) -> QueryResponse:
    """
    知识库上传文件\n
    :param user_file: 用户文件\n
    :param namespace_id: 知识库标识\n
    :return: QueryResponse\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        # 上传文件保存至临时目录
        if user_file.filename is None:
            raise BusinessException(400, "文件名为空")
        filepath = f"{CONTENT_PATH}{user_file.filename}"
        content = await user_file.read()
        print(user_file.filename)
        with open(filepath, "wb") as f:
            f.write(content)
        print(f)
        # 向量标识
        ids = None
        if namespace_id:
            # 根据标识查询知识库信息
            namespaceModel = AiNamespaceDomain().find_by_id(namespace_id)
            if not namespaceModel:
                logger.error(f"[10001]未查询到所属知识库[{namespace_id}]信息")
                raise BusinessException(10001, "未查询到所属知识库信息")
            # 向本地知识库推送元数据
            localRepositoryDomain = LocalRepositoryDomain()
            ids = localRepositoryDomain.push(
                glob=user_file.filename,
                namespaceModel=namespaceModel,
            )
        else:
            # namespace_id 为空时无法确定所属知识库，push 需要 namespaceModel
            raise BusinessException(400, "namespace_id 不能为空")
        # 保存源文件信息
        namespaceFileDomain = AiNamespaceFileDomain()
        namespaceFileDomain.create(
            namespace_id=namespace_id,
            name=user_file.filename,
            display_name=user_file.filename,
            path=CONTENT_PATH,
            type=user_file.content_type or "",
            size=str(user_file.size),
            remark="python",
            vector_ids=ids,
        )
    except BusinessException as business_err:
        logger.error("###API###api_upload_file error, requestId={}, err={}.", request_id, business_err)
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_upload_file error, requestId={}, err={}.", request_id, err)
        response.message = str(err)
        response.status = -1
    return response


@app.post(
    path="/chat/ask",
    tags=["Chat:聊天模块"],
    summary="领域知识问答接口",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
def api_chat_ask(
    ques: str,
    bot_id: str,
    enable_search: bool,
    enable_thinking: bool,
    thinking_budget: int,
    user_id: str | None = None,
    group_uuid: str | None = None,
) -> QueryResponse:
    """
    领域知识问答功能\n
    :param ques: 问题\n
    :param bot_id: 机器人标识\n
    :param enable_search: 是否开启联网搜索\n
    :param enable_thinking: 开启思考模式\n
    :param thinking_budget: 思考过程的最大长度，只在enable_thinking为true时生效\n
    :param user_id: 用户标识\n
    :param group_uuid: 会话分组标识\n
    :return: QueryResponse\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    logger.info("###API###api_chat_ask info, request_id={} bot_id={}, user_id={}, ques={}", request_id, bot_id, user_id, ques)
    try:
        return ChatPrivateDomain(request_id).ask(
            ques=ques,
            bot_id=bot_id,
            user_id=user_id or "",
            group_uuid=group_uuid or "",
            is_want_allow_custom=False,
            enable_search=enable_search,
            enable_thinking=enable_thinking,
            thinking_budget=thinking_budget,
        )
    except BusinessException as business_err:
        logger.error("###API###api_chat_ask error, requestId={}, err={}.", request_id, business_err)
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_chat_ask error, requestId={}, err={}.", request_id, err)
        traceback.print_exc()
        response.message = str(err)
        response.status = -1
    return response


@app.post(
    path="/chat/ask/stream",
    tags=["Chat:聊天模块"],
    summary="领域知识问答接口(Streaming模式)",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
async def api_chat_ask_stream(
    ques: str,
    bot_id: str,
    enable_search: bool,
    enable_thinking: bool,
    thinking_budget: int,
    user_id: str | None = None,
    group_uuid: str | None = None,
):
    """
    领域知识问答功能(Streaming模式)\n
    :param ques: 问题\n
    :param bot_id: 机器人标识\n
    :param enable_search: 是否开启联网搜索\n
    :param enable_thinking: 开启思考模式\n
    :param thinking_budget: 思考过程的最大长度，只在enable_thinking为true时生效\n
    :param user_id: 用户标识\n
    :param group_uuid: 会话分组标识\n
    :return: QueryResponse\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    logger.info("###API###api_chat_ask info, request_id={} bot_id={}, user_id={}, ques={}", request_id, bot_id, user_id, ques)
    try:

        async def event_generator():
            for chatResponse in ChatPrivateDomain(request_id).ask_stream(
                ques=ques,
                bot_id=bot_id,
                user_id=user_id or "",
                group_uuid=group_uuid or "",
                enable_search=enable_search,
                enable_thinking=enable_thinking,
                thinking_budget=thinking_budget,
            ):
                yield chatResponse.json()

        return EventSourceResponse(event_generator())
    except BusinessException as business_err:
        logger.error("###API###api_chat_ask error, requestId={}, err={}.", request_id, business_err)
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_chat_ask error, requestId={}, err={}.", request_id, err)
        traceback.print_exc()
        response.message = str(err)
        response.status = -1
    return response


@app.post(
    path="/chat/public/ask",
    tags=["Chat:聊天模块"],
    summary="公共知识问答接口",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
def api_chat_public_ask(
    ques: str,
    bot_id: str,
    enable_search: bool,
    enable_thinking: bool,
    thinking_budget: int,
    user_id: str | None = None,
    group_uuid: str | None = None,
) -> QueryResponse:
    """
    公共知识问答功能\n
    :param ques: 问题\n
    :param bot_id: 机器人标识\n
    :param enable_search: 是否开启联网搜索\n
    :param enable_thinking: 开启思考模式\n
    :param thinking_budget: 思考过程的最大长度，只在enable_thinking为true时生效\n
    :param user_id: 用户标识\n
    :param group_uuid: 会话分组标识\n
    :return: QueryResponse\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    logger.info("###API###api_chat_public_ask info, request_id={} bot_id={}, user_id={}, ques={}", request_id, bot_id, user_id, ques)
    try:
        return ChatPublicDomain(request_id).ask(
            ques=ques,
            bot_id=bot_id,
            user_id=user_id or "",
            group_uuid=group_uuid or "",
            enable_search=enable_search,
            enable_thinking=enable_thinking,
            thinking_budget=thinking_budget,
        )
    except BusinessException as business_err:
        logger.error("###API###api_chat_public_ask error, requestId={}, err={}.", request_id, business_err)
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_chat_public_ask error, requestId={}, err={}.", request_id, err)
        traceback.print_exc()
        response.message = str(err)
        response.status = -1
    return response


@app.post(
    path="/chat/public/ask/stream",
    tags=["Chat:聊天模块"],
    summary="公共知识问答接口(Streaming模式)",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
async def api_chat_public_ask_stream(
    request: Request,  # 使用Request对象手动处理请求
    ques: str,
    bot_id: str,
    enable_search: bool = False,
    enable_thinking: bool = False,
    enable_ques_optimizer: bool = False,
    enable_quick_qa: bool = False,
    thinking_budget: int = 38912,
    user_id: str | None = None,
    group_uuid: str | None = None,
    voice: int = 0,
):
    """
    公共知识问答功能(Streaming模式)\n
    :param voice:是否语音输入：0-否，1-是。默认非语音输入
    :param enable_quick_qa: 是否开启快速答疑
    :param enable_ques_optimizer: 是否开启问题优化\n
    :param ques: 问题\n
    :param bot_id: 机器人标识\n
    :param enable_search: 是否开启联网搜索\n
    :param enable_thinking: 开启思考模式\n
    :param thinking_budget: 思考过程的最大长度，只在enable_thinking为true时生效\n
    :param user_id: 用户标识\n
    :param group_uuid: 会话分组标识\n
    :return: QueryResponse\n
    """
    # 读取原始请求体
    body = await request.body()

    # 处理空请求体
    if not body:
        request_data = {}
    else:
        # 解析JSON请求体
        request_data = json.loads(body) if body.strip() else {}

    # 提取files参数（如果存在）
    files = request_data.get("files", [])

    response = QueryResponse()
    request_id = str(uuid.uuid4())
    logger.info(
        "###API###api_chat_public_ask_stream info, request_id={} bot_id={}, user_id={}, ques={}, "
        "enable_search={},  enable_thinking={}, enable_ques_optimizer={}, enable_quick_qa={}, thinking_budget={}, files={} ",
        request_id,
        bot_id,
        user_id,
        ques,
        enable_search,
        enable_thinking,
        enable_ques_optimizer,
        enable_quick_qa,
        thinking_budget,
        files,
    )
    try:

        async def event_generator() -> AsyncGenerator[str, None]:
            async for chatResponse in ChatPublicDomain(request_id).ask_chat_stream(
                ques=ques,
                bot_id=bot_id,
                user_id=user_id or "",
                group_uuid=group_uuid or "",
                enable_search=enable_search,
                enable_thinking=enable_thinking,
                enable_ques_optimizer=enable_ques_optimizer,
                enable_quick_qa=enable_quick_qa,
                thinking_budget=thinking_budget,
                files=files,
                voice=voice,
            ):
                yield chatResponse.json()

        return EventSourceResponse(event_generator())
    except BusinessException as business_err:
        logger.error("###API###api_chat_public_ask_stream error, requestId={}, err={}.", request_id, business_err)
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_chat_public_ask_stream error, requestId={}, err={}.", request_id, err)
        traceback.print_exc()
        response.message = str(err)
        response.status = -1
    return response


@app.post(
    path="/chat/history",
    tags=["Chat:聊天模块"],
    summary="查询指定用户的历史聊天记录",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
def api_chat_history(
    bot_id: str,
    user_id: str,
) -> QueryResponse:
    """
    查询指定用户的历史聊天记录\n
    :param bot_id: 机器人标识\n
    :param user_id: 用户标识\n
    :return: QueryResponse\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        # 根据标识查询机器人配置信息
        chatBotModel = AiChatBotDomain().find_one(bot_id=bot_id)
        # 查询历史聊天记录
        chatHistoryDomain = AiChatHistoryDomain()
        history = chatHistoryDomain.find_all_by_id(user_id=user_id, bot_id=bot_id)
        data = {"bot": chatBotModel, "history": history}
        response.data = data
    except BusinessException as business_err:
        logger.error("###API###api_chat_history error, requestId={}, err={}.", request_id, business_err)
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_chat_history error, requestId={}, err={}.", request_id, err)
        response.message = str(err)
        response.status = -1
    return response


@app.post(
    path="/bot/public/init",
    tags=["Bot:机器人模块"],
    summary="初始化公共知识机器人",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
def api_init_public_bot() -> QueryResponse:
    """
    初始化公共知识机器人\n
    :return: QueryResponse\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        BotInitDomain(request_id=request_id).init_bot_list()
    except BusinessException as business_err:
        logger.error("###API###api_init_public_bot error, requestId={}, err={}.", request_id, business_err)
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_init_public_bot error, requestId={}, err={}.", request_id, err)
        response.message = str(err)
        response.status = -1
    return response


@app.get(
    path="/bot",
    tags=["Bot:机器人模块"],
    summary="查询机器人列表信息",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
def api_get_bot(id: str | None = None, bot_id: str | None = None) -> QueryResponse:
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        bot_list = AiChatBotDomain(request_id=request_id).find_all(
            id=id or "",
            bot_id=bot_id or "",
        )
        response.data = {"bot_list_length": len(bot_list), "bot_list": bot_list}
    except BusinessException as business_err:
        logger.error("###API###api_get_bot error, requestId={}, err={}.", request_id, business_err)
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_get_bot error, requestId={}, err={}.", request_id, err)
        response.message = str(err)
        response.status = -1
    return response


@app.get(
    path="/bot/{bot_id}",
    tags=["Bot:机器人模块"],
    summary="查询机器人详情信息",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
def api_get_bot_info(
    bot_id: str,
) -> QueryResponse:
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        chatBotModel = AiChatBotDomain(request_id=request_id).find_one(bot_id=bot_id)
        setattr(chatBotModel, "namespace", AiNamespaceDomain(request_id=request_id).find_by_id(namespace_id=chatBotModel.namespace_id))
        response.data = chatBotModel
    except BusinessException as business_err:
        logger.error("###API###api_get_bot_info error, requestId={}, err={}.", request_id, business_err)
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_get_bot_info error, requestId={}, err={}.", request_id, err)
        response.message = str(err)
        response.status = -1
    return response


@app.get(
    path="/namespace",
    tags=["Namespace:知识库模块"],
    summary="查询知识库列表信息",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
def api_get_namespace(
    id: str | None = None,
    user_id: str | None = None,
    type: str | None = None,
    name: str | None = None,
    namespace: str | None = None,
) -> QueryResponse:
    """
    查询全部知识库列表\n
    :param id: 主键标识\n
    :param user_id: 专属用户\n
    :param type: 知识库类型\n
    :param name: 知识库名称\n
    :param namespace: 知识库空间\n
    :return: 知识库列表\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        namespace_list = AiNamespaceDomain(request_id=request_id).find_all(
            id=id or "",
            user_id=user_id or "",
            type=type or "",
            name=name or "",
            namespace=namespace or "",
        )
        response.data = {
            "namespace_list_length": len(namespace_list),
            "namespace_list": namespace_list,
        }
    except BusinessException as business_err:
        logger.error("###API###api_get_namespace error, requestId={}, err={}.", request_id, business_err)
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_get_namespace error, requestId={}, err={}.", request_id, err)
        response.message = str(err)
        response.status = -1
    return response


@app.get(
    path="/namespace/{namespace_id}",
    tags=["Namespace:知识库模块"],
    summary="查询知识库详情信息",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
def api_get_namespace_info(
    namespace_id: str,
) -> QueryResponse:
    """
    查询知识库详情信息\n
    :param namespace_id: 主键标识\n
    :return: 知识库详情\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        response.data = AiNamespaceDomain(request_id=request_id).find_by_id(namespace_id=namespace_id)
        setattr(response.data, "file_list", AiNamespaceFileDomain(request_id=request_id).find_by_condition(namespace_id=namespace_id))
    except BusinessException as business_err:
        logger.error("###API###api_get_namespace_info error, requestId={}, err={}.", request_id, business_err)
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_get_namespace_info error, requestId={}, err={}.", request_id, err)
        response.message = str(err)
        response.status = -1
    return response


@app.get(
    path="/namespace/{namespace_id}/file",
    tags=["Namespace:知识库模块"],
    summary="查询知识库所属文件列表",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
def api_get_namespace_file(
    namespace_id: str,
) -> QueryResponse:
    """
    查询知识库所属文件列表\n
    :param namespace_id: 主键标识\n
    :return: 文件列表\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        response.data = AiNamespaceFileDomain(request_id=request_id).find_by_condition(namespace_id=namespace_id)
    except BusinessException as business_err:
        logger.error("###API###api_get_namespace_file error, requestId={}, err={}.", request_id, business_err)
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_get_namespace_file error, requestId={}, err={}.", request_id, err)
        response.message = str(err)
        response.status = -1
    return response


@app.get(
    path="/namespace/{namespace_id}/file/{file_id}",
    tags=["Namespace:知识库模块"],
    summary="查询知识库所属的指定文件详情",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
def api_get_namespace_file_info(
    namespace_id: str,
    file_id: str,
) -> QueryResponse:
    """
    查询知识库所属的指定文件详情\n
    :param namespace_id: 主键标识\n
    :param file_id: 文件标识\n
    :return: 文件详情信息\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        namespaceModel = AiNamespaceDomain(request_id=request_id).find_by_id(namespace_id=namespace_id)
        if not namespaceModel:
            return response

        namespaceFileModel = AiNamespaceFileDomain(request_id=request_id).find_by_id(file_id=file_id)
        if not namespaceFileModel:
            return response

        ids = str(namespaceFileModel.vector_ids).split(",") if namespaceFileModel.vector_ids else []
        vector_list = get_instance_client().query_data(namespace=namespaceModel.namespace, ids=ids)
        vector_list_result = [{"uuid": v.uuid, "collection_id": v.collection_id, "custom_id": v.custom_id, "document": v.document, "metadata": v.cmetadata} for v in vector_list]
        response.data = namespaceFileModel
        setattr(response.data, "namespace", namespaceModel)
        setattr(response.data, "vector_list_length", len(vector_list_result))
        setattr(response.data, "vector_list", vector_list_result)
    except BusinessException as business_err:
        logger.error("###API###api_get_namespace_file_info error, requestId={}, err={}.", request_id, business_err)
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_get_namespace_file_info error, requestId={}, err={}.", request_id, err)
        response.message = str(err)
        response.status = -1
    return response


@app.post(
    path="/namespace/file",
    tags=["Namespace:知识库模块"],
    summary="删除知识库所属的指定文件向量数据",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
def api_del_namespace_file_data(
    param: DelChunkParam,
) -> QueryResponse:
    """
    删除知识库所属的指定文件向量数据\n
    :param: 需要删除分片的相关信息
    :return: None\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        # 分别查询知识库和指定文件的信息
        namespaceModel = AiNamespaceDomain(request_id=request_id).find_by_id(namespace_id=param.namespace_id)
        namespaceFileModel = AiNamespaceFileDomain(request_id=request_id).find_by_id(file_id=param.file_id)
        if namespaceFileModel.namespace_id != param.namespace_id:
            logger.error(
                "Namespace ERROR, [{}]指定文件[{}]所属知识库标识不匹配, DB[{}] PARAM[{}], request_id={}.", ERROR_10207, param.file_id, namespaceFileModel.namespace_id, param.namespace_id, request_id
            )
            raise BusinessException(ERROR_10207.code, ERROR_10207.message)
        ids_model = str(namespaceFileModel.vector_ids).split(",") if namespaceFileModel.vector_ids else []
        # 是要删除整个文件
        if param.is_want_deleted_file:
            # 删除向量数据
            api_del_vector_namespace_data(namespace=namespaceModel.namespace, ids=ids_model)
            # 更新业务数据
            AiNamespaceFileDomain(request_id=request_id).update(
                file_id=int(param.file_id),
                vector_ids=[],
                vector_status="Done",
                vector_count=0,
                deleted=1 if param.is_want_deleted_file else 0,
            )
        else:
            # 删除向量数据
            api_del_vector_namespace_data(namespace=namespaceModel.namespace, ids=param.ids)
            ids_array = [i for i in ids_model if i not in param.ids]
            # 更新业务数据
            AiNamespaceFileDomain(request_id=request_id).update(
                file_id=int(param.file_id),
                vector_ids=ids_array,
                vector_status="Done",
                vector_count=0,
                deleted=1 if (param.is_null_deleted_file and len(ids_array) == 0) else 0,
            )
    except BusinessException as business_err:
        logger.error("###API###api_del_namespace_file_data error, requestId={}, err={}.", request_id, business_err)
        traceback.print_exc()
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_del_namespace_file_data error, requestId={}, err={}.", request_id, err)
        traceback.print_exc()
        response.message = str(err)
        response.status = -1
    return response


@app.post(
    path="/vector/del/namespace",
    tags=["Vector:向量模块"],
    summary="删除命名空间的所有向量数据",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
def api_del_vector_namespace(namespace: str) -> QueryResponse:
    """
    删除命名空间的所有向量数据\n
    :param namespace: 命名空间\n
    :return: QueryResponse\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        vector_client = get_instance_client()
        vector_client.delete_data(namespace=namespace, delete_all=True)
    except BusinessException as business_err:
        logger.error("###API###api_del_vector_namespace error, requestId={}, err={}.", request_id, business_err)
        traceback.print_exc()
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_del_vector_namespace error, requestId={}, err={}.", request_id, err)
        traceback.print_exc()
        response.message = str(err)
        response.status = -1
    return response


@app.post(
    path="/vector/del/namespace/data",
    tags=["Vector:向量模块"],
    summary="删除命名空间的指定向量标识的数据",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
def api_del_vector_namespace_data(
    namespace: str,
    ids: list[str],
) -> QueryResponse:
    """
    删除命名空间的指定向量数据\n
    :param namespace: 命名空间\n
    :param ids: 向量标识集合\n
    :return: QueryResponse\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        logger.info("###API###api_del_vector_namespace_data INFO, requestId={}, ids={}", request_id, ids)
        if ids and len(ids) > 0 and ids[0] != "None":
            vector_client = get_instance_client()
            vector_client.delete_data(namespace=namespace, ids=ids)
    except BusinessException as business_err:
        logger.error("###API###api_del_vector_namespace_data error, requestId={}, err={}.", request_id, business_err)
        traceback.print_exc()
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_del_vector_namespace_data error, requestId={}, err={}.", request_id, err)
        traceback.print_exc()
        response.message = str(err)
        response.status = -1
    return response


@app.post(
    path="/vector/del/namespace/file",
    tags=["Vector:向量模块"],
    summary="删除命名空间的指定文件标识的数据",
    response_model=QueryResponse,
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
)
def api_del_vector_namespace_file(
    param: DelFileParam,
) -> QueryResponse:
    """
    删除命名空间的指定文件标识的数据\n
    :param : 删除相关文件信息内容体
    :return: QueryResponse\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())
    try:
        logger.info("###API###api_del_vector_namespace_file INFO, requestId={}, file_id_list={}", request_id, param.file_id_list)
        get_instance_client().delete_file_data(namespace=param.namespace, file_id_list=param.file_id_list)
    except BusinessException as business_err:
        logger.error("###API###api_del_vector_namespace_file error, requestId={}, err={}.", request_id, business_err)
        traceback.print_exc()
        response.message = business_err.message
        response.status = business_err.code
    except Exception as err:
        logger.error("###API###api_del_vector_namespace_file error, requestId={}, err={}.", request_id, err)
        traceback.print_exc()
        response.message = str(err)
        response.status = -1
    return response


@app.post(
    path="/llm/ragas/upload",
    tags=["Ragas:结果评估"],
    summary="结果评估",
    response_description="返回体对象[status:结果状态(0成功), message:错误信息, data:业务数据]",
    response_model=None,
)
async def api_ragas_upload_file(user_file: UploadFile = File(...)) -> QueryResponse | StreamingResponse:
    """
    答案评估\n
    :param user_file: 答案文件，问题|标准答案|LLM答案|分片1|分片2|分片3|分片4|...\n
    :return: QueryResponse\n
    """
    response = QueryResponse()
    request_id = str(uuid.uuid4())

    # 这些依赖在部分部署场景可能是可选的；使用动态导入避免静态检查直接报错。
    # 若缺少依赖，在运行期给出明确错误信息。
    from importlib import import_module
    from typing import Any

    try:
        pd: Any = import_module("pandas")
        Dataset: Any = import_module("datasets").Dataset
        ragas_module: Any = import_module("ragas")
        evaluate: Any = ragas_module.evaluate
        ragas_metrics: Any = import_module("ragas.metrics")
        answer_relevancy: Any = ragas_metrics.answer_relevancy
        context_precision: Any = ragas_metrics.context_precision
        context_recall: Any = ragas_metrics.context_recall
        faithfulness: Any = ragas_metrics.faithfulness
    except ModuleNotFoundError as err:
        raise BusinessException(500, f"缺少依赖 {err.name}，请安装后重试") from err
    except ImportError as err:
        raise BusinessException(500, f"依赖导入失败：{err}") from err

    from starlette.responses import StreamingResponse

    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY or ""
    try:
        # 上传文件保存至临时目录
        if user_file.filename is None:
            raise BusinessException(400, "文件名为空")
        filepath = f"{CONTENT_PATH}{user_file.filename}"
        content = await user_file.read()
        print(user_file.filename)
        with open(filepath, "wb") as f:
            f.write(content)

        print(filepath)
        # 读取Excel文件
        df = pd.read_excel(filepath, header=None)

        questions = []
        ground_truths = []
        answers = []
        contexts = []
        # 循环输出每行每列的值
        for index, row in df.iterrows():
            if index == 0:
                continue
            contexts_sub = []
            for column in row.index:
                if column == 0:
                    questions.append(row[column])
                elif column == 1:
                    ground_truths.append([row[column]])
                elif column == 2:
                    answers.append(row[column])
                else:
                    contexts_sub.append(row[column])
            contexts.append(contexts_sub)
        print(questions)
        data = {"question": questions, "answer": answers, "contexts": contexts, "ground_truths": ground_truths}
        # Convert dict to dataset
        dataset = Dataset.from_dict(data)
        result = evaluate(
            dataset=dataset,
            metrics=[
                context_precision,
                context_recall,
                faithfulness,
                answer_relevancy,
            ],
        )
        df_result = result.to_pandas()
        df_result = df_result  # type: ignore[assignment]
        io_csv = StringIO()
        df_result.to_csv(io_csv, index=False, encoding="utf-8", errors="ignore")  # type: ignore[attr-defined]
        io_csv.seek(0)
        stream_resp = StreamingResponse(iter([io_csv.getvalue()]), media_type="text/csv")
        filename_stem = user_file.filename.split(".")[0]
        logger.info("filename:{}", filename_stem)
        stream_resp.headers["Content-Disposition"] = "attachment; filename=result.csv"
        logger.info(
            "###API###api_ragas_upload_file info, requestId={},fileName={},result={}",
            request_id,
            user_file.filename,
            df_result.to_json(),  # type: ignore[attr-defined]
        )
        return stream_resp
    except BusinessException as business_err:
        logger.error("###API###api_ragas_upload_file error, requestId={}, err={}.", request_id, business_err)
        response.message = business_err.message
        response.status = business_err.code
        return response
    except Exception as err:
        logger.error("###API###api_ragas_upload_file error, requestId={}, err={}.", request_id, err)
        response.message = str(err)
        response.status = -1
        return response


if __name__ == "__main__":
    uvicorn.run(app="api:app", host="0.0.0.0", port=8062, reload=True, workers=100)
