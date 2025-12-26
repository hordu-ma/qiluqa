import uuid
from typing import List, Tuple
from langchain.memory import ConversationBufferMemory
from langchain.schema import Document
from custom.amway.amway_config import *
from custom.amway.prepare.service.prepare_docs_services import PrepareDocs
from custom.amway.allm.baidubce.baidubce_client import BaidubceClient
from service.domain.ai_chat_history import ChatHistoryModel


def get_prepare_docs(
        ques_docs: List[Tuple[Document, float]]
) -> List[Tuple[Document, float]]:
    """
    封装知识库文档列表
    :return: 知识库文档列表
    """
    if not ques_docs or len(ques_docs) == 0:
        return ques_docs
    return PrepareDocs(ques_docs=ques_docs).get_new_ques_docs()


def get_prepare_answer(
        ques_docs: List[Tuple[Document, float]]
):
    """
    获取预制回答
    :param ques_docs: 知识库文档列表
    :return: 预制回答
    """
    if not ques_docs or len(ques_docs) == 0:
        return None
    if AMWAY_PREPARE_ANSWER:
        document = ques_docs[0][0]
        if document and document.metadata and document.metadata.get("answer"):
            return document.metadata.get("answer")
    return None


def get_memory(
    history: List[ChatHistoryModel] = None,
    memory_history_key: str = "chat_history",
    memory_input_key: str = "question"
) -> ConversationBufferMemory:
    """
    封装历史聊天记录
    :param history: 历史聊天记录
    :param memory_history_key:  长程记忆-历史记录占位符字段
    :param memory_input_key: 长程记忆-输入信息占位符字段
    :return: 长程记忆对象
    """
    if AMWAY_HISTORY_CUSTOM_ENABLED:
        memory = ConversationBufferMemory(
            memory_key=memory_history_key,
            input_key=memory_input_key,
            human_prefix=AMWAY_HISTORY_CUSTOM_PREFIX_Q,
            ai_prefix=AMWAY_HISTORY_CUSTOM_PREFIX_A,
        )
    else:
        memory = ConversationBufferMemory(
            memory_key=memory_history_key,
            input_key=memory_input_key
        )
    if history and len(history) > 0:
        # history转memory倒叙处理
        for h in history[::-1]:
            memory.chat_memory.add_user_message(h.question)
            memory.chat_memory.add_ai_message(h.answer)
    return memory


def chat_from_baidubce(
        ques: str,
        history: List[ChatHistoryModel] = None,
        request_id: str = str(uuid.uuid4()),
):
    """
    千帆大模型问答服务
    :param ques: 问题
    :param history: 历史聊天记录
    :param request_id: 请求唯一标识
    :return: 回答
    """
    baidubceClient = BaidubceClient(request_id=request_id)
    answer, is_secure_flag = baidubceClient.chat(ques=ques, history=history)
    return answer, is_secure_flag

