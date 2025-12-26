from typing import Any, List, Mapping, Optional
import requests
from loguru import logger
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
from langchain.llms.utils import enforce_stop_tokens


class ChatGlmAI(LLM):

    url: str = "http://10.143.33.239:8001"
    temperature: float = 0.4
    max_length: int = 2048
    top_p: float = 0.8
    history: List[List[str]] = None

    @property
    def _default_params(self) -> Mapping[str, Any]:
        return {
            "temperature": self.temperature,
            "max_length": self.max_length,
            "top_p": self.top_p,
            "history": self.history,
        }

    @property
    def _llm_type(self) -> str:
        return "chatglm"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        headers = {
            "Content-Type": "application/json"
        }
        json = {"prompt": prompt, **self._default_params, **kwargs}
        logger.info("#############Request Amway ChatGLM2 LLMs INFO, url={}, headers={}, json={}.",
                    self.url, headers, json)
        response = requests.post(
            url=self.url,
            headers=headers,
            json=json,
        )
        response_json = response.json()
        logger.info("#############Request Amway ChatGLM2 LLMs INFO, response={}.", response_json)
        answer = response_json["response"]
        if stop is not None:
            answer = enforce_stop_tokens(answer, stop)
        return answer
