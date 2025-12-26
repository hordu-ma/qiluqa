import dashscope
from config.base_config_dashscope import BASHSCOPE_API_KEY


class QwenVL:

    def __init__(
            self,
            model: str = "qwen-vl-plus",
            api_key: str = BASHSCOPE_API_KEY
    ):
        self.model = model
        self.api_key = api_key

    def call(self, ques: str, image: str):
        messages = [
            {
                "role": "user",
                "content": [
                    {"image": image},
                    {"text": ques}
                ]
            }
        ]
        return dashscope.MultiModalConversation.call(
            model=self.model,
            api_key=self.api_key,
            messages=messages
        )
