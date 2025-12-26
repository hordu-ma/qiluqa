import re
import uuid
import json
from datetime import datetime
from langchain.schema import Document
from loguru import logger
from typing import List, Tuple, Any
from config.base_config import MEMORY_LIMIT_SIZE, CHUNK_IMAGE_LABELS, TRACE_SUFFIX_LIST, CHUNK_IMAGE_NAS_LABELS
from content.filter_book import filter_history_list
from custom.amway.amway_config import AMWAY_ENABLED
from framework.business_code import ERROR_10008
from framework.business_except import BusinessException
from service.domain.ai_chat_bot import ChatBotModel, chatbot_has_traceability
from service.domain.ai_chat_history import AiChatHistoryDomain, ChatHistoryModel
from service.domain.ai_chat_history_files_summary import AiChatHistoryFilesSummaryDomain
from service.domain.ai_namespace import NamespaceModel
from service.domain.ai_namespace_file import AiNamespaceFileDomain
from service.chat_response import ChatResponse, ChatResponseVO
from service.schedule.disclaimer_data_schedule import sort_disclaimer_data
from service.schedule.prohibited_data_schedule import get_prohibited_data


class BaseChatMessage:
    """
    聊天消息基础处理
    """

    def __init__(
            self,
            request_id: str = str(uuid.uuid4())
    ):
        """
        构造函数
        :param request_id: 请求唯一标识
        """
        self.request_id = request_id

    @classmethod
    def placeholder(
            cls,
            chatBotModel: ChatBotModel,
            request_id: str = str(uuid.uuid4()),
            is_want_delete: bool = True,
            **kwargs
    ):
        prompt = str(chatBotModel.prompt)
        pattern = "{(?:business?|system)[.][A-Za-z0-9_]+}"
        prompt_placeholder = re.findall(pattern, prompt)
        if not prompt_placeholder:
            return
        prompt_placeholder_list = [str(p).split(".")[1].split("}")[0] for p in prompt_placeholder]
        prompt_placeholder_key_map = {str(p).split(".")[1].split("}")[0]: p for p in prompt_placeholder}
        prompt_placeholder_map = {}
        for ppl in prompt_placeholder_list:
            if ppl not in kwargs:
                if is_want_delete:
                    prompt = prompt.replace("{business." + ppl + "}", "").replace("{system." + ppl + "}", "")
                else:
                    logger.error(
                        "BaseChatMessage placeholder ERROR, [{}]机器人[{}]提示词缺少占位符信息[{}], request_id={}.",
                        ERROR_10008, chatBotModel.bot_id, ppl, request_id)
                    raise BusinessException(ERROR_10008.code, ERROR_10008.message + "[" + ppl + "]")
            else:
                prompt_placeholder_map[ppl] = kwargs[ppl]
        for k, v in prompt_placeholder_map.items():
            key = prompt_placeholder_key_map[k]
            val = '' if not v else v
            prompt = prompt.replace(key, val)
        chatBotModel.prompt = prompt

    @classmethod
    def get_metadata_list(cls, ques_docs: List[Tuple[Document, float, str]]):
        metadata = []
        input_documents = []
        for _doc, _score, _file_id in ques_docs:
            input_documents.append(_doc)
            _doc.metadata["score"] = _score
            _doc.metadata["content"] = _doc.page_content
            metadata.append(_doc.metadata)
        return metadata, input_documents

    @classmethod
    def get_label_content(cls, metadata: List[dict]) -> str:
        """
        封装图表标签
        :param metadata: 分片元数据
        :return: 图表标签
        """
        labels = []
        label_content = ""
        for m in metadata:
            if "images" in m and m["images"]:
                for ims in m["images"]:
                    if ims["name"] not in labels:
                        labels.append(ims["name"])
                        name = "表" + ims["mark_num"]
                        if "nas" in ims["path"]:
                            label = str(CHUNK_IMAGE_NAS_LABELS).replace("{path}", ims["path"]).replace("{name}", name)
                        else:
                            label = str(CHUNK_IMAGE_LABELS).replace("{path}", ims["name"]).replace("{name}", name)
                        label_content = label_content + "\n\n" + label
        label_content = "" if not labels else label_content
        return label_content

    def get_trace_content(
            self,
            file_id_list: List[str],
            input_documents: List[Document],
    ) -> List[str]:
        """
        封装溯源信息
        :param file_id_list: 知识库标识列表
        :param input_documents: 文档列表
        :return: 溯源信息
        """
        request_id = str(uuid.uuid4())
        contents = set()
        # 利用集合属性将知识库标识列表中重复的field_id去除
        new_id_list = list(set(file_id_list)) if file_id_list else []
        new_id_list = [s for s in new_id_list if s != ""]
        logger.info("####get_trace_content_data INFO，new_id_list={}.", new_id_list)
        try:
            if new_id_list:
                for file_id in new_id_list:
                    namespaceFileModel = AiNamespaceFileDomain(request_id=request_id).find_by_id(file_id=file_id)
                    trace_name = namespaceFileModel.trace_name
                    contents.add(trace_name)
            else:
                for _doc in input_documents:
                    if "name" in _doc.metadata and _doc.metadata["name"] not in contents:
                        contents.add(_doc.metadata["name"])
            return [
                self.get_trace_content_remove_suffix(str(c))
                for c in contents
            ]
        except Exception as err:
            logger.warning(err)
            logger.info("####get_trace_content_data INFO，request_id={}, file_id_list={}.", request_id, file_id_list)

    @staticmethod
    def recognize_contents(contents):
        """
        判断溯源文件的数量，如果数量大于1
        则在除最后一本溯源文件的结尾加'、'
        """
        logger.info("####recognize_contents INFO, contents={}.", contents)
        contents_update = []
        length = len(contents)
        if length > 1:
            for i in range(length - 1):
                data = contents[i] + '、'
                contents_update.append(data)
            contents_update.append(contents[length - 1])
        else:
            return contents
        return contents_update

    def get_answer_has_trace_content(
            self,
            answer: str,
            chatBotModel: ChatBotModel,
            namespaceModel: NamespaceModel,
            ques_docs: List[Tuple[Document, float, str]],
            input_documents: List[Document],
    ) -> str:
        """
        查询免责声明与溯源文件信息
        并将两个信息与answer组装起来
        """
        if not chatbot_has_traceability(chatBotModel):
            return answer
        # 查询溯源信息
        trace_content = []
        if ques_docs:
            file_id_list = [_file_id for doc, _score, _file_id in ques_docs]
            trace_content = self.get_trace_content(file_id_list=file_id_list, input_documents=input_documents)
            trace_content = self.recognize_contents(contents=trace_content)
        # 查询免责信息
        has_trace_text, not_trace_text = sort_disclaimer_data(namespaceModel=namespaceModel)
        # 封装溯源免责
        if trace_content:
            answer = answer + "\n" + has_trace_text.replace("{trace_content}", "".join(trace_content))
        else:
            answer = answer + "\n" + not_trace_text
        return answer

    @classmethod
    def get_trace_content_remove_suffix(cls, content: str) -> str:
        """
        溯源信息后缀处理
        :param content: 溯源信息
        :return: 溯源信息
        """
        for suffix in TRACE_SUFFIX_LIST:
            content = content.replace(suffix, "")
        return content

    @classmethod
    def query_chat_history(
            cls,
            request_id: str,
            user_id: str,
            bot_id: str,
            group_uuid: str = None,
            memory_limit_size: int = MEMORY_LIMIT_SIZE
    ) -> List[ChatHistoryModel]:
        """
        查询历史聊天记录
        :param request_id: 请求唯一标识
        :param user_id: 用户标识
        :param bot_id: 机器人标识
        :param group_uuid: 会话标识
        :param memory_limit_size: 长程记忆配置
        :return: 历史聊天记录
        """
        chatHistoryDomain = AiChatHistoryDomain(request_id=request_id)
        if not group_uuid:
            return chatHistoryDomain.find_last_by_id(
                user_id=user_id,
                bot_id=bot_id,
                limit_size=memory_limit_size
            )
        else:
            return chatHistoryDomain.find_last_by_id(
                user_id=user_id,
                bot_id=bot_id,
                limit_size=memory_limit_size,
                group_uuid=group_uuid
            )

    @classmethod
    def query_chat_history_files_summary(
            cls,
            request_id: str,
            history: List[ChatHistoryModel] = [],
    ) -> str:
        """
        查询历史聊天记录关联的附件摘要记录
        :param request_id: 请求唯一标识
        :param history: 历史记录
        :return: 历史聊天附件摘要汇总结果
        """
        chatHistoryFilesSummaryDomain = AiChatHistoryFilesSummaryDomain(request_id=request_id)
        if history and len(history) > 0:
            history_ids = [str(item.id) for item in history if item is not None and str(item.id).strip()]
            summarys = chatHistoryFilesSummaryDomain.find_all_by_history_ids(history_ids=history_ids)
            summary_contents = [str(item.summary) for item in summarys if item is not None and str(item.summary).strip()] if summarys and len(summarys) > 0 else []
            return "".join(summary_contents)
        return ""

    @classmethod
    def purge_with_history(
            cls,
            ques: str,
            answer: str,
            bot_id: str,
            user_id: str,
            question_time: datetime = datetime.now(),
            chatHistoryDomain: AiChatHistoryDomain = AiChatHistoryDomain(),
            **kwargs
    ) -> ChatResponse:
        """
        问答结果清洗并保留历史聊天记录
        :param ques: 问题
        :param answer: 回答
        :param bot_id: 机器人标识
        :param user_id: 用户标识
        :param question_time: 问答时间点
        :param chatHistoryDomain: 历史聊天记录实体服务类
        :return: 问答结果
        """
        # 敏感词|智能策略
        #       new_answer = cls.purge(answer=answer)
        # 保存历史聊天记录
        chatResponse = cls.save_history_message(
            ques=ques,
            answer=answer,
            bot_id=bot_id,
            user_id=user_id,
            question_time=question_time,
            chatHistoryDomain=chatHistoryDomain,
            **kwargs,
        )

        # 保存附件的summary信息，关联历史记录，后续跟历史记录同步召回使用
        if kwargs.get("files_context") and chatResponse and chatResponse.data and chatResponse.data.history_id:
            cls.save_history_files(files_context=kwargs.get("files_context"), history_id=chatResponse.data.history_id)

        return chatResponse

    @classmethod
    def purge(
            cls,
            answer: str,
    ) -> str:
        """
        问答结果清洗逻辑
        :param answer: 回答
        :return: 问答结果
        """
        if not answer:
            return answer
        prohibited_List = get_prohibited_data()
        for prohibited in prohibited_List.values():
            try:
                prohibited = eval(prohibited)
                if prohibited["ruleType"] == '1':
                    # 敏感词直接替换
                    answer = answer.replace(prohibited['prohibited'], prohibited['replacement'])
                elif prohibited["ruleType"] == '0':
                    # 敏感词正则替换
                    answer = re.sub(prohibited['regularExpression'], prohibited['replacement'], answer)
            except Exception as e:
                logger.warning("###Purge###: e={} prohibited={}.", e, prohibited)
        # 智能策略 - 超链接格式处理
        url_pattern = "(?:https?|ftp|file)://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]"
        url_collection = re.findall(url_pattern, answer)
        for url in url_collection:
            answer = answer.replace(url, " " + url + " ")
        return answer

    @classmethod
    def save_history_message(
            cls,
            ques: str,
            answer: str,
            bot_id: str,
            user_id: str,
            question_time: datetime = datetime.now(),
            chatHistoryDomain: AiChatHistoryDomain = AiChatHistoryDomain(),
            **kwargs
    ) -> ChatResponse:
        """
        保存历史聊天记录
        :param ques: 问题
        :param answer: 回答
        :param bot_id: 机器人标识
        :param user_id: 用户标识
        :param question_time: 问答时间点
        :param chatHistoryDomain: 历史聊天记录实体服务类
        :return: 问答结果
        """
        scene = None
        group_uuid = None
        use_mark = None
        answer_type = None
        label_list = []
        comment = ""
        metadata = []
        slave_result = []
        answer_list = []
        llms = ""
        llms_model_name = ""
        total_tokens = 0
        input_tokens = 0
        output_tokens = 0
        search = []
        thinking = ""
        files = []
        voice = 0
        for k, v in kwargs.items():
            if k == "scene":
                scene = v
            if k == "group_uuid":
                group_uuid = v
            if k == "use_mark":
                use_mark = v
            if k == "answer_type":
                answer_type = v
            if k == "label_list":
                label_list = v
            if k == "comment":
                comment = v
            if k == "metadata":
                metadata = v
            if k == "slave_result":
                slave_result = v
            if k == "answer_list":
                answer_list = v
            if k == "llms":
                llms = v
            if k == "llms_model_name":
                llms_model_name = v
            if k == "total_tokens":
                total_tokens = int(v)
            if k == "input_tokens":
                input_tokens = int(v)
            if k == "output_tokens":
                output_tokens = int(v)
            if k == "thinking":
                thinking = v
            if k == "search":
                search = v
            if k == "files":
                files = v
            if k == "voice":
                voice = v

        # 绿网策略 - 历史记录过滤不满意内容
        is_want_save_history = True
        for cts in filter_history_list:
            if cts in answer:
                is_want_save_history = False
                break

        history_id = 0
        if user_id:
            deleted = 0 if is_want_save_history else 1
            history_id = chatHistoryDomain.create(
                user_id=user_id,
                bot_id=bot_id,
                question=ques,
                answer=answer,
                question_time=question_time,
                deleted=deleted,
                group_uuid=group_uuid,
                use_mark=use_mark,
                answer_type=answer_type,
                comment=comment,
                llms=llms,
                llms_model_name=llms_model_name,
                total_tokens=total_tokens,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                thinking=thinking,
                search=json.dumps(search, ensure_ascii=False) if search else "",
                files=json.dumps(files, ensure_ascii=False) if files else "",
                voice=voice,
            )
        return ChatResponse(
            data=ChatResponseVO(
                answer=answer,
                history_id=history_id,
                scene=scene,
                metadata=metadata,
                slave_result=slave_result,
                answer_list=answer_list,
                label_list=label_list,
            )
        )

    @classmethod
    def save_history_files(
            cls,
            files_context: str = None,
            history_id: str = None,
            chatHistoryFilesSummaryDomain: AiChatHistoryFilesSummaryDomain = AiChatHistoryFilesSummaryDomain(),
    ):
        """
        保存历史聊天附件summary信息
        :param chatHistoryFilesSummaryDomain:
        :param files_context: 聊天附件summary信息
        :param history_id: 历史聊天记录id
        """
        # 保存附件的summary信息，关联历史记录，后续跟历史记录同步召回使用
        if not files_context or not history_id:
            return

        summary_id = chatHistoryFilesSummaryDomain.create(history_id=history_id,summary=files_context)
        return summary_id

    @classmethod
    def is_dict_with_usage(cls, chunk: Any):
        try:
            if chunk:
                usage = chunk.get("usage")
                if "total_tokens" in usage and "input_tokens" in usage and "output_tokens" in usage:
                    return True, usage
            return False, None
        except Exception:
            return False, None

    @classmethod
    def is_dict_with_usage_metadata(cls, usage_metadata: Any, usage: dict):
        if usage_metadata:
            if "total_tokens" in usage_metadata:
                usage["total_tokens"] = usage.get("total_tokens") + usage_metadata["input_tokens"]
            if "input_tokens" in usage_metadata:
                usage["input_tokens"] = usage.get("input_tokens") + usage_metadata["input_tokens"]
            if "output_tokens" in usage_metadata:
                usage["output_tokens"] = usage.get("output_tokens") + usage_metadata["output_tokens"]
