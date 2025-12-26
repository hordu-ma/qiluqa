from typing import Any, List, Mapping, Optional, Dict
import requests
import json
from loguru import logger
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
from custom.amway.amway_config import (
    BAIDUBCE_ACCESS_TOKEN_URL,
    BAIDUBCE_CHAT_URL,
    BAIDUBCE_TEMPERATURE,
    BAIDUBCE_TOP_P,
    BAIDUBCE_PENALTY_SCORE, BAIDUBCE_SECURE_ANSWER,
)
from framework.business_code import ERROR_10901, ERROR_10902
from framework.business_except import BusinessException


class BaidubceAI(LLM):

    access_token_url: str = BAIDUBCE_ACCESS_TOKEN_URL
    chat_url: str = BAIDUBCE_CHAT_URL
    temperature: float = BAIDUBCE_TEMPERATURE
    top_p: float = BAIDUBCE_TOP_P
    penalty_score: float = BAIDUBCE_PENALTY_SCORE
    history: List[List[str]] = None
    system_role: str = None

    @property
    def _llm_type(self) -> str:
        return "baidubce"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        payload = ""
        logger.info("###BaidubceAI get_access_token request INFO, url={}, body={}.", self.access_token_url, payload)
        response = requests.post(url=self.access_token_url, data=payload, headers=headers)
        logger.info("###BaidubceAI get_access_token request INFO, response={}.", response.text)
        if "error" in response.text:
            logger.error("###BaidubceAI get_access_token request ERROR, code={}, message={}.", ERROR_10901, response.text)
            raise BusinessException(ERROR_10901.code, ERROR_10901.message)
        data = eval(response.text)
        access_token = str(data["access_token"])
        chat_url = self.chat_url.replace("{access_token}", access_token)
        headers = {
            'Content-Type': 'application/json',
        }
        body = {
            "messages": self._get_messages(prompt=prompt, **kwargs),
            "temperature": self.temperature,
            "top_p": self.top_p,
            "penalty_score": self.penalty_score,
        }
        logger.info("###BaidubceAI chat request INFO, url={}, ques={}, body={}.", chat_url, prompt, body)
        response = requests.post(url=chat_url, data=json.dumps(body), headers=headers)
        response_json = response.json()
        logger.info("###BaidubceAI chat request INFO, response={}.", response_json)
        # 千帆业务异常
        if "error_code" in response_json:
            logger.error("###BaidubceAI chat request ERROR, code={}, message={}.", ERROR_10902, response_json)
            raise BusinessException(response_json["error_code"], response_json["error_msg"])
        # 千帆安全风险
        if bool(response_json["need_clear_history"]) and "result" not in response_json:
            if "retry" not in kwargs:
                return self.__call__(prompt=prompt, retry=False, **kwargs)
            return BAIDUBCE_SECURE_ANSWER
        return response_json["result"]

    def _get_messages(
            self,
            prompt: str,
            **kwargs: Any,
    ) -> List[Dict]:
        # 从扩展参数中获取重试参数标识
        retry = True
        for k, v in kwargs.items():
            if k == "retry":
                retry = v
                break

        messages = [{"role": "system", "content": self.system_role}]
        if self.history and len(self.history) > 0 and retry:
            for h in self.history[::-1]:
                messages.append({
                    "role": "user",
                    "content": self.system_role
                })
                messages.append({
                    "role": "assistant",
                    "content": h[1]
                })
        messages.append({
            "role": "user",
            "content": prompt
        })
        return messages


if __name__ == "__main__":
    print(BaidubceAI().__call__(prompt="习近平的级别"))
