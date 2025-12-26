from typing import List, Optional, Any
import requests
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
import time
import jwt
from loguru import logger
from config.base_config_chatglm4 import *


class ChatGlm4AI(LLM):
    llm_model_name: str = CHATGLM4_MODEL_NAME
    top_p: float = CHATGLM4_TOP_P
    temperature: float = CHATGLM4_TEMPERATURE
    max_tokens: int = CHATGLM4_MAX_TOKENS
    url: str = CHATGLM4_URL
    api_key: str = CHATGLM4_API_KEY
    question: str = None
    history: List[List[str]] = None
    system_role: str = None

    @property
    def _llm_type(self) -> str:
        return "chatglm4"

    def _call(
            self,
            prompt: str,
            exp_seconds=60,
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
    ) -> str:
        authorization = ChatGlm4AI().generate_token(self.api_key, exp_seconds)
        headers = {
            "Content-Type": "application/json",
            "Authorization": authorization
        }

        messages = [{"role": "system", "content": self.system_role}]
        if prompt:
            messages.append({
                "role": "user",
                "content": prompt,
            })
            if self.history and len(self.history) > 0:
                for h in self.history[::-1]:
                    messages.append({
                        "role": "user",
                        "content": h[0],
                    })
                    messages.append({
                        "role": "assistant",
                        "content": h[1],
                    })
                messages.append({
                    "role": "user",
                    "content": self.question,
                })

        json = {
            "model": self.llm_model_name,
            "messages": messages,
            "top_p": self.top_p,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        },

        logger.info("#############Request ChatGLM4 LLMs INFO, url={}, headers={}, json={}.", self.url, headers, json)
        response = requests.post(url=self.url, headers=headers, json=json[0])
        response_json = response.json()
        logger.info("#############Request ChatGLM4 LLMs INFO, httpstatus={}, response={}.", response.status_code,
                    response_json)

        if response.status_code != 200:
            return "[" + response_json["error"]["code"] + "]" + response_json["error"]["message"]
        return response_json.get("choices", [{}])[0].get("message", "").get("content", "")

    @classmethod
    def generate_token(cls, apikey: str, exp_seconds: int) -> str:
        try:
            id, secret = apikey.split(".")
        except Exception as e:
            raise Exception("invalid apikey", e)

        payload = {
            "api_key": id,
            "exp": int(round(time.time() * 1000)) + exp_seconds * 1000,
            "timestamp": int(round(time.time() * 1000)),
        }

        return jwt.encode(
            payload,
            secret,
            algorithm="HS256",
            headers={"alg": "HS256", "sign_type": "SIGN"},
        )


if __name__ == "__main__":
    print(ChatGlm4AI().__call__(prompt='2023年12月1日的天气怎么样'))
