import json
import uuid
from datetime import datetime
from typing import Iterator, List, Dict, AsyncIterator

from langchain_core.messages import AIMessageChunk, AIMessage
from loguru import logger

from config.base_config import HTTP_HOST, QUES_OPTIMIZER_MODEL, QUES_OPTIMIZER_MODEL_NAME, FILES_SUMMARY_MODEL, \
    FILES_SUMMARY_MODEL_NAME, INTENTION_RECOGNITION_MODEL, INTENTION_RECOGNITION_MODEL_NAME, THINKING_MODEL_NAME, \
    THINKING_MODEL
from config.base_config_model_type import MODEL_TYPE_VL, MODEL_TYPE_TEXT
from custom.bespin.bespin_sample_service import SampleService
from framework.business_code import ERROR_10007, ERROR_10000
from framework.business_except import BusinessException
from models.chains.chain_model import ChainModel
from service.base_chat_message import BaseChatMessage
from service.chat_response import ChatResponse, ChatResponseVO
from service.domain.ai_chat_bot import AiChatBotDomain
from service.domain.ai_chat_history import AiChatHistoryDomain
from service.intention_recognition import MedicalDiagnosisChecker
from service.map_reduce_summarizer import MapReduceSummarizer
from service.medical_question_optimizer import MedicalQuestionOptimizer
from service.search_service import SearchService

IMAGES_SUMMARY_FIXED_QUES = """
请对上传的图片按顺序逐一识别，输出需严格遵循以下规则，**重点确保多张图片中所有关键信息无遗漏，同时禁止任何重复内容**：
1. **文本类图片（如报告、病历、标签等）**：
   - 执行OCR功能时，按图片内原始排版（如表格行/列、项目编号顺序）逐行/逐项提取所有可见文字，包括但不限于：检查项目名称、读数、单位、参考范围、异常标注（↑/↓/异常等）。
   - 必须明确列出每一项信息，**禁止使用任何概括性语句省略内容**（如“其余正常”“以上为主要项目”均不允许），即使项目重复或结果正常也需完整呈现。
   - **呈现所有文本内容即可，无需对识别到的文本内容进行推理总结**。
2. **非文本类图片（如影像、解剖图、场景图等）**：
   - 按视觉优先级列出关键信息：先标注图片类型（如“胸部CT影像”“膝关节X光片”），再描述核心可见元素（如“左肺上叶有直径约1.5cm结节”“图中显示心电监护仪屏幕及数值”）。
   - 确保覆盖图片中所有医学相关元素，不遗漏任何可识别的关键特征（如病灶位置、器械名称、解剖结构等）。
3. **多图处理强制规则**：
   - 每张图片单独成段，开头用“图片X：”（X为顺序编号，如“图片1：”“图片2：”）明确区分。
   - 处理完当前图片后，需默认检查是否有遗漏信息（如文本类是否漏项、非文本类是否漏关键元素），确认完整后再开始处理下一张。
   - 不同图片的信息完全独立，互不干扰，不交叉引用。
4.**通用约束**：
   - 所有输出需紧扣图片原始信息，确保关键内容无遗漏，同时精简表述，避免冗余描述；
所有输出需以“可追溯”为核心，确保任何信息都能对应到原始图片的具体位置，同时保持表述精简，不添加非必要内容。
"""

FILE_SUMMARY_FIXED_QUES = """
1. **核心要求：完整性与准确性**  
   - 必须完整保留所有关键信息：包括核心结论、重要论据、逻辑链条关键环节，以及**全部明确数据**（具体数值、百分比、时间、数量、对比数据等）。  
   - 数据对比、异常值、限定条件（如“在XX前提下”“仅适用于XX情况”）需原样呈现，不得省略。  
   - 所有信息（尤其是数据）与原文完全一致，专业术语、特定概念保留原文表述，仅在可能引起歧义时补充极简解释（不超过10字）。
2. **结构性适配**  
   - 严格遵循原文逻辑结构（如“问题-分析-结论”“分项罗列”等），分项内容逐一对应总结，不合并、不省略任何分项的核心要素。  
   - 用清晰的层级关系（如序号、分点）区分不同部分，确保关联性明确。
3. **精简原则**  
   - 仅删减重复表述、冗余修饰语（如无关形容词、多次重复的相同前提），但需保证保留信息独立可读，不因精简导致逻辑断裂。  
   - 避免任何主观解读或额外延伸，仅客观还原原文关键信息。
请直接输出总结内容，确保读者通过总结可完整掌握原文所有关键信息（包括每一项具体数据和核心结论）。
"""


class ChatPublicDomain(BaseChatMessage):
    """
    公共知识问答服务
    """

    def __init__(
            self,
            request_id: str = str(uuid.uuid4()),
    ):
        """
        构造方法
        :param request_id: 请求唯一标识
        """
        super().__init__(request_id)
        self.request_id = request_id

    def ask(
            self,
            ques: str,
            bot_id: str,
            user_id: str = None,
            group_uuid: str = None,
            **kwargs,
    ) -> ChatResponse:
        """
        公共知识问答
        :param ques: 问题
        :param bot_id: 机器人标识
        :param user_id: 用户标识
        :param group_uuid: 会话分组标识
        :return: AI回答内容
        """
        question_time = datetime.now()
        # 根据标识查询机器人配置信息
        chatBotModel = AiChatBotDomain(self.request_id).find_one(bot_id=bot_id)
        logger.info("ChatPublicDomain INFO, request_id={}, 当前机器人信息：{}.", self.request_id, chatBotModel)
        if not chatBotModel:
            logger.error("ChatPublicDomain ERROR, [{}]未查询到机器人[{}]信息, request_id={}.", ERROR_10000, bot_id,
                         self.request_id)
            raise BusinessException(ERROR_10000.code, ERROR_10000.message)
        if not chatBotModel.is_public_bot():
            logger.error("ChatPublicDomain ERROR, [{}]当前机器人[{}]的使用类型不合法, request_id={}.", ERROR_10007,
                         bot_id, self.request_id)
            raise BusinessException(ERROR_10007.code, ERROR_10007.message)

        # 查询历史聊天记录
        history = self.query_chat_history(
            request_id=self.request_id,
            user_id=user_id,
            bot_id=bot_id,
            memory_limit_size=chatBotModel.memory_limit_size,
            group_uuid=group_uuid
        )
        logger.info("ChatPublicDomain INFO, request_id={}, 当前历史聊天记录：{}.", self.request_id, history)

        # 样例插件
        ques, sub_ques = SampleService(request_id=self.request_id).plugin(
            ques=ques,
            chatBotModel=chatBotModel,
            history=ChainModel.init_memory(history=history)[1]
        )

        # 发起问答
        chain = ChainModel.get_instance(question=sub_ques, chatBotModel=chatBotModel, history=history)
        logger.info("ChatPublicDomain INFO, request_id={}, chain.prompt={}.", self.request_id, chain.prompt)
        answer = chain.predict(question=sub_ques)

        logger.info("ChatPublicDomain INFO, request_id={}, 问题=[{}], 回答结果=[{}].", self.request_id, ques, answer)
        return self.purge_with_history(
            ques=ques,
            answer=answer,
            bot_id=bot_id,
            user_id=user_id,
            question_time=question_time,
            chatHistoryDomain=AiChatHistoryDomain(self.request_id),
            group_uuid=group_uuid,
        )

    def ask_stream(
            self,
            ques: str,
            bot_id: str,
            user_id: str = None,
            group_uuid: str = None,
            **kwargs,
    ) -> Iterator[ChatResponse]:
        """
        公共知识问答
        :param ques: 问题
        :param bot_id: 机器人标识
        :param user_id: 用户标识
        :param group_uuid: 会话分组标识
        :return: AI回答内容
        """
        question_time = datetime.now()
        # 根据标识查询机器人配置信息
        chatBotModel = AiChatBotDomain(self.request_id).find_one(bot_id=bot_id)
        logger.info("ChatPublicDomain INFO, ask_stream request_id={}, 当前机器人信息：{}.", self.request_id,
                    chatBotModel)
        if not chatBotModel:
            logger.error("ChatPublicDomain ERROR, ask_stream [{}]未查询到机器人[{}]信息, request_id={}.", ERROR_10000,
                         bot_id, self.request_id)
            raise BusinessException(ERROR_10000.code, ERROR_10000.message)
        if not chatBotModel.is_public_bot():
            logger.error("ChatPublicDomain ERROR, ask_stream [{}]当前机器人[{}]的使用类型不合法, request_id={}.",
                         ERROR_10007, bot_id, self.request_id)
            raise BusinessException(ERROR_10007.code, ERROR_10007.message)

        llms, llm_model_name = ChainModel.get_llms_model(chatBotModel, MODEL_TYPE_TEXT)

        # 意图识别
        checker = MedicalDiagnosisChecker(model=llms, model_name=llm_model_name)
        intention_response = checker.get_response(ques)
        if intention_response:
            answers = [intention_response, "[DONE]"]
            for ans in answers:
                if ans != "[DONE]":
                    chat_response = self.purge_with_history(
                        ques=ques,
                        answer=ans,
                        bot_id=bot_id,
                        user_id=user_id,
                        question_time=question_time,
                        chatHistoryDomain=AiChatHistoryDomain(self.request_id),
                        group_uuid=group_uuid,
                        llms=chatBotModel.llms,
                        llms_model_name=llm_model_name,
                    )
                    chat_response.data.answer = ans
                    yield chat_response
                else:
                    # 返回结束符
                    yield ChatResponse(
                        data=ChatResponseVO(
                            answer=ans,
                        )
                    )
            return

        # 查询历史聊天记录
        history = self.query_chat_history(
            request_id=self.request_id,
            user_id=user_id,
            bot_id=bot_id,
            memory_limit_size=chatBotModel.memory_limit_size,
            group_uuid=group_uuid
        )
        logger.info("ChatPublicDomain INFO, ask_stream request_id={}, 当前历史聊天记录：{}.", self.request_id, history)

        # 样例插件
        ques, sub_ques = SampleService(request_id=self.request_id).plugin(
            ques=ques,
            chatBotModel=chatBotModel,
            history=ChainModel.init_memory(history=history)[1]
        )

        # 聊天附件处理
        images = []
        files = kwargs.get("files")
        if files:
            for file_info in kwargs.get("files"):
                fileName = file_info.get("fileName")
                fileSize = file_info.get("fileSize")
                filePath = file_info.get("filePath")
                preprocessedFilePath = file_info.get("preprocessedFilePath")
                fileType = file_info.get("fileType")
                logger.info(f"收到文件: {fileName}")
                logger.info(f"文件大小: {fileSize} 字节")
                logger.info(f"文件路径: {filePath}")
                logger.info(f"预处理后路径: {preprocessedFilePath}")
                logger.info(f"文件类型: {fileType}")
                if fileType == "img":
                    images.append(filePath if filePath and ":" in filePath else HTTP_HOST + filePath)

        # 处理模型类型
        model_type = MODEL_TYPE_VL if images and len(images) > 0 else MODEL_TYPE_TEXT

        # 发起问答
        chain = ChainModel.get_instance_stream(question=sub_ques, chatBotModel=chatBotModel, history=history,
                                               model_type=model_type, images=images, **kwargs)
        logger.info("ChatPublicDomain INFO, ask_stream request_id={}, chain.prompt={}.", self.request_id, "?")
        # 增加联网搜索内容
        input_context = []
        search: List[Dict] = []
        search_context = []
        if kwargs.get("enable_search"):
            input_results, query_results = SearchService().get_tavily_search_list(ques)
            search = list(query_results)
            search_context.append(input_results)
        answer = ""
        thinking = ""
        is_first = True
        for chunk in chain.stream({"question": sub_ques, "context": input_context, "search_context": search_context,
                                   "chat_history": " "}):
            search_: List[Dict] = []
            if is_first:
                search_ = list(search)
                is_first = False
            chunk = json.loads(chunk) if chunk else chunk
            flag, usage = self.is_dict_with_usage(chunk)
            answer = answer if flag else answer + chunk.get("content")
            answer_ = "[DONE]" if flag else chunk.get("content")
            thinking_ = chunk.get("thinking")
            thinking += thinking_
            if answer_ == "[DONE]":
                chat_response = self.purge_with_history(
                    ques=ques,
                    answer=answer,
                    bot_id=bot_id,
                    user_id=user_id,
                    question_time=question_time,
                    chatHistoryDomain=AiChatHistoryDomain(self.request_id),
                    group_uuid=group_uuid,
                    llms=chatBotModel.llms,
                    llms_model_name=chatBotModel.get_llm_model_name(),
                    thinking=thinking,
                    search=search,
                    files=files,
                    **usage,
                )
                chat_response.data.answer = answer_
                chat_response.data.thinking = thinking_
                chat_response.data.search = search_
                yield chat_response
            else:
                yield ChatResponse(
                    data=ChatResponseVO(
                        answer=answer_,
                        thinking=thinking_,
                        search=search_
                    )
                )
        logger.info(
            "ChatPublicDomain INFO, ask_stream request_id={}, 问题=[{}], 回答结果=[{}],思考过程=[{}],搜索结果=[{}].",
            self.request_id, ques, answer, thinking, search)

    async def ask_chat_stream(
            self,
            ques: str,
            bot_id: str,
            user_id: str = None,
            group_uuid: str = None,
            enable_ques_optimizer: bool = False,
            **kwargs,
    ) -> AsyncIterator[ChatResponse]:
        """
        公共知识问答-聊天模型
        :param enable_ques_optimizer: 是否开启问题优化
        :param ques: 问题
        :param bot_id: 机器人标识
        :param user_id: 用户标识
        :param group_uuid: 会话分组标识
        :return: AI回答内容
        """
        question_time = datetime.now()
        # 根据标识查询机器人配置信息
        chatBotModel = AiChatBotDomain(self.request_id).find_one(bot_id=bot_id)
        logger.info("ChatPublicDomain INFO, ask_stream request_id={}, 当前机器人信息：{}.", self.request_id,
                    chatBotModel)
        if not chatBotModel:
            logger.error("ChatPublicDomain ERROR, ask_stream [{}]未查询到机器人[{}]信息, request_id={}.", ERROR_10000,
                         bot_id, self.request_id)
            raise BusinessException(ERROR_10000.code, ERROR_10000.message)
        if not chatBotModel.is_public_bot():
            logger.error("ChatPublicDomain ERROR, ask_stream [{}]当前机器人[{}]的使用类型不合法, request_id={}.",
                         ERROR_10007, bot_id, self.request_id)
            raise BusinessException(ERROR_10007.code, ERROR_10007.message)

        llms, llm_model_name = ChainModel.get_llms_model(chatBotModel, MODEL_TYPE_TEXT)

        # 查询历史聊天记录
        history = self.query_chat_history(
            request_id=self.request_id,
            user_id=user_id,
            bot_id=bot_id,
            memory_limit_size=chatBotModel.memory_limit_size,
            group_uuid=group_uuid
        )
        logger.info("ChatPublicDomain INFO, ask_stream request_id={}, 当前历史聊天记录：{}.", self.request_id, history)

        # 将所有question通过换行符拼接
        combined_questions = '\n'.join([item.question for item in history])

        # 图片识别前置，识别的内容参与意图识别
        # 聊天附件处理
        files, images, preprocessedFiles = await self.handle_files(kwargs)

        # VL模型处理图片
        vl_answer = await self.invoke_images(chatBotModel, images, kwargs, IMAGES_SUMMARY_FIXED_QUES)

        # 意图识别
        intention_ques = vl_answer + combined_questions + ques
        checker = MedicalDiagnosisChecker(model=INTENTION_RECOGNITION_MODEL, model_name=INTENTION_RECOGNITION_MODEL_NAME)
        intention_response = checker.get_response(intention_ques)
        if intention_response:
            answers = [intention_response, "[DONE]"]
            for ans in answers:
                if ans != "[DONE]":
                    chat_response = self.purge_with_history(
                        ques=ques,
                        answer=ans,
                        bot_id=bot_id,
                        user_id=user_id,
                        question_time=question_time,
                        chatHistoryDomain=AiChatHistoryDomain(self.request_id),
                        group_uuid=group_uuid,
                        llms=chatBotModel.llms,
                        llms_model_name=llm_model_name,
                        voice=kwargs.get("voice"),
                    )
                    chat_response.data.answer = ans
                    yield chat_response
                else:
                    # 返回结束符
                    yield ChatResponse(
                        data=ChatResponseVO(
                            answer=ans,
                        )
                    )
            return

        # 查询历史聊天附件summary记录
        history_files_summary = self.query_chat_history_files_summary(
            request_id=self.request_id,
            history=history,
        )
        logger.info("ChatPublicDomain INFO, ask_stream request_id={}, 当前历史聊天关联的附件摘要信息：{}.", self.request_id, history_files_summary)

        # 样例插件
        ques, sub_ques = SampleService(request_id=self.request_id).plugin(
            ques=ques,
            chatBotModel=chatBotModel,
            history=ChainModel.init_memory(history=history)[1]
        )

        # # 问题优化
        # opt_ques = sub_ques
        # if enable_ques_optimizer:
        #     optimizer = MedicalQuestionOptimizer(model=QUES_OPTIMIZER_MODEL, model_name=QUES_OPTIMIZER_MODEL_NAME)
        #     opt_ques = optimizer.optimize_question(sub_ques)
        #     logger.info("ChatPublicDomain INFO, ask_stream request_id={}, sub_ques={}, opt_ques={}.", self.request_id, sub_ques, opt_ques)

        # 文本模型处理文件
        files_answer = await self.invoke_files(preprocessedFiles, FILE_SUMMARY_FIXED_QUES)
        files_context = files_answer + vl_answer

        # 合并历史会话附件内容与当前的附件内容
        final_files_context = "<历史附件信息>" + history_files_summary + "</历史附件信息><当前问题附件信息>" + files_context + "</当前问题附件信息>"

        # 处理模型类型
        answer = ""
        thinking = ""
        search = ""
        usage = {"total_tokens": 0, "input_tokens": 0, "output_tokens": 0}
        logger.info("ChatPublicDomain INFO, ask_stream request_id={}, chain.prompt={}.", self.request_id, "?")
        # 开启联网搜索模式
        if kwargs.get("enable_search"):
            # 代理模型
            agent = ChainModel.get_chat_agent_instance_stream(chatBotModel=chatBotModel, history=history, **kwargs)
            async for event in agent.astream_events({"question": sub_ques,
                                                     "files_context": final_files_context,
                                                     "chat_history": ""}, version="v2"):
                kind = event["event"]
                answer_ = ""
                thinking_ = ""
                has_think = False
                # LLM 开始生成文本（逐字输出）
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    is_thinking = chunk.response_metadata.get("is_thinking", False)
                    is_answer = chunk.response_metadata.get("is_answer", False)
                    BaseChatMessage.is_dict_with_usage_metadata(chunk.usage_metadata, usage)
                    content = chunk.content
                    if content == "<think>":
                        has_think = True
                        continue
                    if content == "</think>":
                        has_think = False
                        continue
                    if content:
                        if is_answer and not has_think:
                            answer += content
                            answer_ = content
                        if is_thinking or has_think:
                            thinking += content
                            thinking_ = content
                        yield ChatResponse(
                            data=ChatResponseVO(
                                answer=answer_,
                                thinking=thinking_,
                                search=[]
                            )
                        )
                    finish_reason = chunk.response_metadata.get("finish_reason", "") == "stop"
                    if finish_reason:
                        answer_ = "[DONE]"
                        chat_response = BaseChatMessage.purge_with_history(
                            ques=sub_ques,
                            answer=answer,
                            bot_id=bot_id,
                            user_id=user_id,
                            question_time=question_time,
                            chatHistoryDomain=AiChatHistoryDomain(self.request_id),
                            group_uuid=group_uuid,
                            llms=chatBotModel.llms,
                            llms_model_name=chatBotModel.get_llm_model_name(),
                            thinking=thinking,
                            search=search,
                            files=files,
                            files_context=files_context,
                            voice=kwargs.get("voice"),
                            **usage,
                        )
                        chat_response.data.answer = answer_
                        chat_response.data.thinking = thinking_
                        chat_response.data.search = []
                        yield chat_response
                # 代理决定调用工具（显示加载状态）
                elif kind == "on_tool_start":
                    tool_name = event["name"]
                    logger.info("[正在调用工具: {}]...", tool_name)
                # 工具返回结果后继续流式输出
                elif kind == "on_tool_end":
                    search_ = event["data"]["output"]
                    search = search_
                    yield ChatResponse(
                        data=ChatResponseVO(
                            answer=answer_,
                            thinking=thinking_,
                            search=search_
                        )
                    )
        else:
            chain = ChainModel.get_chat_instance_stream(chatBotModel=chatBotModel, history=history, **kwargs)
            has_think = False
            for chunk in chain.stream({"question": sub_ques, "files_context": final_files_context, "chat_history": ""}):
                chunk: AIMessageChunk = chunk
                is_thinking = chunk.response_metadata.get("is_thinking", False)
                is_answer = chunk.response_metadata.get("is_answer", False)
                if chunk.content == "<think>":
                    has_think = True
                    continue
                if chunk.content == "</think>":
                    has_think = False
                    continue
                answer_ = ""
                thinking_ = ""
                BaseChatMessage.is_dict_with_usage_metadata(chunk.usage_metadata, usage)
                content = chunk.content
                if content:
                    if is_answer and not has_think:
                        answer += content
                        answer_ = content
                    if is_thinking or has_think:
                        thinking += content
                        thinking_ = content
                    yield ChatResponse(
                        data=ChatResponseVO(
                            answer=answer_,
                            thinking=thinking_,
                            search=[]
                        )
                    )
                finish_reason = chunk.response_metadata.get("finish_reason", "") == "stop"
                if finish_reason:
                    answer_ = "[DONE]"
                    chat_response = BaseChatMessage.purge_with_history(
                        ques=sub_ques,
                        answer=answer,
                        bot_id=bot_id,
                        user_id=user_id,
                        question_time=question_time,
                        chatHistoryDomain=AiChatHistoryDomain(self.request_id),
                        group_uuid=group_uuid,
                        llms=chatBotModel.llms,
                        llms_model_name=chatBotModel.get_llm_model_name(),
                        thinking=thinking,
                        search=search,
                        files=files,
                        files_context=files_context,
                        voice=kwargs.get("voice"),
                        **usage,
                    )
                    chat_response.data.answer = answer_
                    chat_response.data.thinking = thinking_
                    chat_response.data.search = []
                    yield chat_response
        logger.info(
            "ChatPublicDomain INFO, ask_stream request_id={}, 问题=[{}], 回答结果=[{}],思考过程=[{}],搜索结果=[{}].",
            self.request_id, ques, answer, thinking, search)

    async def handle_files(self,  kwargs):
        """
        处理聊天附件信息，输出总结后的结果
        :param chatBotModel:
        :param kwargs:
        :param ques:
        :return:
        """
        images = []
        preprocessedFiles = []
        files = kwargs.get("files")
        if files:
            for file_info in kwargs.get("files"):
                fileName = file_info.get("fileName")
                filePath = file_info.get("filePath")
                preprocessedFilePath = file_info.get("preprocessedFilePath")
                fileType = file_info.get("fileType")
                if fileType == "img":
                    images.append(filePath if filePath and ":" in filePath else HTTP_HOST + filePath)
                if fileType == "file" and preprocessedFilePath:
                    preprocessedFiles.append({"fileName": fileName, "filePath": preprocessedFilePath})
        return files, images, preprocessedFiles

    async def invoke_images(self, chatBotModel, images, kwargs, ques):
        """
        处理聊天图片信息，通过调用VL模型进行图片识别+理解，得到图片解读后的文本信息
        :param chatBotModel:
        :param images:
        :param kwargs:
        :param ques:
        :return:
        """
        if images and len(images) > 0 and ChainModel.check_llm_model_existing(chatBotModel=chatBotModel,
                                                                              model_type=MODEL_TYPE_VL):
            llms, llm_model_name = ChainModel.get_llms_model(chatBotModel, MODEL_TYPE_VL)
            chain = ChainModel.get_chat_instance_stream_common(prompt=ques, model=llms, model_name= llm_model_name, model_type=MODEL_TYPE_VL,
                                                        images=images, **kwargs)
            logger.info("invoke_images images={}", images)
            response = chain.invoke(input={})
            logger.info("invoke_images result={}", response)
            response: AIMessage = response
            return "<图片内容>" + response.content + "</图片内容>" if response and response.content else ""
        return ""

    async def invoke_files(self, files, ques):
        """
        处理聊天文件信息，将相关的聊天文件，逐个分块进行总结，得到最后的summary结果
        :param files:
        :param ques:
        :return:
        """
        filesContents = ""
        if files and len(files) > 0:
            summarizer = MapReduceSummarizer(model=FILES_SUMMARY_MODEL, model_name=FILES_SUMMARY_MODEL_NAME)
            contents = summarizer.get_content(files=files, question=ques)
            logger.info("summarizer.get_content result={}", contents)
            if contents and len(contents) > 0:
                for content in contents:
                    filesContents += "<" + content["fileName"] + ">" + content["content"] + "</" + content["fileName"] + ">"
        return "<文件内容>" + filesContents + "</文件内容>" if filesContents else ""
