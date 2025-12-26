import os
from typing import Any, List, Mapping, Optional
import requests
from loguru import logger
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM


class ChatGlm3AI(LLM):

    url: str = os.environ.get("AMWAY_CHATGLM3_URL") or "http://10.143.33.239:8002/v1/chat/completions"
    model: str = "chatglm3-6b"
    max_tokens: int = 2048
    temperature: float = 0.4
    top_p: float = 0.8
    history: List[List[str]] = None

    @property
    def _default_params(self) -> Mapping[str, Any]:
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }

    @property
    def _llm_type(self) -> str:
        return "chatglm3-6b"

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
        messages = []
        if self.history and len(self.history) > 0:
            for h in self.history[::-1]:
                messages.append({
                    "role": "user",
                    "content": h[0]
                })
                messages.append({
                    "role": "assistant",
                    "content": h[1]
                })
        messages.append({
            "role": "user",
            "content": prompt,
        })

        json = {"prompt": prompt, "messages": messages, **self._default_params, **kwargs}
        logger.info("#############Request Amway ChatGLM3 LLMs INFO, url={}, headers={}, json={}.", self.url, headers, json)
        response = requests.post(
            url=self.url,
            headers=headers,
            json=json,
        )
        response_json = response.json()
        logger.info("#############Request Amway ChatGLM3 LLMs INFO, response={}.", response_json)
        return response_json.get("choices", [{}])[0].get("message", "").get("content", "")
