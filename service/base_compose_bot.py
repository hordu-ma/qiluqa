import uuid
from typing import Dict, List
from langchain.schema import Document
from models.chains.chain_model import ChainModel
from service.base_chat_message import BaseChatMessage
from service.domain.ai_chat_bot import ChatBotModel, AiChatBotDomain


class BaseComposeBot:
    """
    组合机器人功能的超类
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
    def split_slave_bot(
            cls,
            chatBotModel: ChatBotModel
    ):
        """
        切分组装从属机器人信息
        :param chatBotModel: 机器人模型对象
        :return: 从属机器人
        """
        slave_bot_dict = {}
        if chatBotModel.is_master_type() and chatBotModel.slave_bot_mark:
            model_list = chatBotModel.slave_bot_mark.split(",")
            for model in model_list:
                _models = tuple(model.split(":"))
                if len(_models) == 2:
                    slave_bot_dict[_models[0]] = _models[1]
        return slave_bot_dict

    def send_ques_by_slave_bot(
            self,
            ques: str,
            chatBotModel: ChatBotModel,
            input_documents: list[Document] = None,
            **kwargs,
    ) -> List[Dict]:
        """
        调度发起从属机器人的固定问题推理
        :param ques: 用户问题
        :param chatBotModel: 机器人模型对象
        :param input_documents: 召回的知识库文档
        :param kwargs: 扩展信息
        :return:
        """
        slave_result = []
        slave_bot_dict = self.split_slave_bot(chatBotModel=chatBotModel)
        for k, v in slave_bot_dict.items():
            _chatBot = AiChatBotDomain(self.request_id).find_one(bot_id=k)
            if _chatBot:
                # 提示词占位符处理
                BaseChatMessage.placeholder(
                    chatBotModel=_chatBot,
                    request_id=self.request_id,
                    **kwargs,
                )
                fixed_ques = ques if not _chatBot.fixed_ques else _chatBot.fixed_ques
                if _chatBot.is_public_bot():
                    chain = ChainModel.get_instance(chatBotModel=_chatBot, question=fixed_ques)
                    answer = chain.predict(question=fixed_ques)
                    answer = BaseChatMessage.purge(answer)
                    if not slave_result:
                        slave_result = [{
                            "bot_id": k,
                            "field": v,
                            "answer": answer
                        }]
                    else:
                        slave_result.append({
                            "bot_id": k,
                            "field": v,
                            "answer": answer
                        })
                    continue
                elif _chatBot.is_private_bot():
                    chain = ChainModel.get_document_instance(chatBotModel=_chatBot, question=ques, **kwargs)
                    answer = chain.run(question=fixed_ques, input_documents=input_documents)
                    answer = BaseChatMessage.purge(answer)
                    if not slave_result:
                        slave_result = [{
                            "bot_id": k,
                            "field": v,
                            "answer": answer
                        }]
                    else:
                        slave_result.append({
                            "bot_id": k,
                            "field": v,
                            "answer": answer
                        })
                    continue
                else:
                    pass
        return slave_result
