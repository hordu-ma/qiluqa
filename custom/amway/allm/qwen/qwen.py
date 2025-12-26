from typing import Any, List, Mapping, Optional
import requests
from loguru import logger
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
from custom.amway.amway_config import (
    AI_QWEN_MODEL_BASE_URL,
    AI_QWEN_MODEL_NAME,
    AI_QWEN_OUTPUT_TOKEN_LENGTH,
    AI_QWEN_TEMPERATURE, AI_QWEN_TOP_P, AI_QWEN_TOP_K
)


class QwenAI(LLM):

    url: str = AI_QWEN_MODEL_BASE_URL
    model: str = AI_QWEN_MODEL_NAME
    max_length: int = AI_QWEN_OUTPUT_TOKEN_LENGTH
    temperature: float = AI_QWEN_TEMPERATURE
    top_p: float = AI_QWEN_TOP_P
    top_k: int = AI_QWEN_TOP_K
    history: List[List[str]] = None

    @property
    def _default_params(self) -> Mapping[str, Any]:
        return {
            "model": self.model,
            "max_length": self.max_length,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
        }

    @property
    def _llm_type(self) -> str:
        return "qwen"

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
        logger.info("#############Request Amway QWEN72B LLMs INFO, url={}, headers={}, json={}.", self.url, headers, json)
        response = requests.post(
            url=self.url,
            headers=headers,
            json=json,
        )
        response_json = response.json()
        logger.info("#############Request Amway QWEN72B LLMs INFO, response={}.", response_json)
        return response_json.get("choices", [{}])[0].get("message", "").get("content", "")
