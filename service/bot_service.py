import uuid

from content.prompt_template import prompt_template_list
from service.domain.ai_chat_bot import AiChatBotDomain

suffix_prompt = """
{chat_history}

问题: {question}

Answer:"""


class BotInitDomain:

    def __init__(
            self,
            request_id: str = str(uuid.uuid4())
    ):
        """
        构造函数
        :param request_id: 请求唯一标识
        """
        self.request_id = request_id

    def init_bot_list(self):
        """
        初始化公共知识机器人
        :return: None
        """
        # 查询现有机器人列表
        chatBotDomain = AiChatBotDomain(self.request_id)
        bot_domain_list = [domain.name for domain in chatBotDomain.find_all()]
        # 匹配新增机器人
        for pt in prompt_template_list:
            if pt["name"] not in bot_domain_list:
                chatBotDomain.create(
                    bot_id=str(uuid.uuid4()).replace('-', ''),
                    name=pt["name"],
                    welcome_tip=pt["welcome_tip"],
                    prompt=pt["prompt"]+suffix_prompt,
                    prompt_variables="question,chat_history",
                )


