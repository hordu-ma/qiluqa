import json
import random
import time
import uuid
from typing import Any, List, Optional, Iterator, Mapping
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
from langchain_core.outputs import GenerationChunk
from loguru import logger
from openai import OpenAI

from config.base_config import DEFAULT_CHAT_BOT_ROLE
from config.base_config_deepseek import *


class DeepseekAI(LLM):

    url: str = DEEPSEEK_URL
    llm_model_name: str = DEEPSEEK_MODEL_NAME
    max_tokens: int = int(DEEPSEEK_MAX_TOKENS)
    temperature: float = float(DEEPSEEK_TEMPERATURE)
    request_id: str = str(uuid.uuid4())
    system_role: str = DEFAULT_CHAT_BOT_ROLE
    kwargs: dict[str, Any] = None

    def __init__(self, *args: Any, **kwargs: Any):
        """
        构造函数
        :param args: 参数
        :param kwargs: 扩展参数
        """
        super().__init__(*args, **kwargs)
        self.kwargs = kwargs

    @property
    def _llm_type(self) -> str:
        return "Deepseek"

    @property
    def _default_params(self) -> Mapping[str, Any]:
        return {
            "model": self.llm_model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

    def _call(
            self,
            prompt: str,
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
    ) -> str:
        """
        常规推理
        :return: 推理结果
        """
        api_key = random.choices(DEEPSEEK_API_KEY_POOL[0], DEEPSEEK_API_KEY_POOL[1], k=1)[0]
        client = OpenAI(api_key=api_key, base_url=self.url)
        messages = [
            {"role": "system", "content": self.system_role},
            {"role": "user", "content": prompt},
        ]
        if self.kwargs.get("enable_thinking"):
            extra_body = {"enable_thinking": True, "chat_template_kwargs": {"enable_thinking": True}}
        else:
            extra_body = {"enable_thinking": False, "chat_template_kwargs": {"enable_thinking": False}}
        logger.info("#############Request {} LLMs Call INFO, request_id={}, url={}, params={}, message={}, extra_body={}.",
                    self._llm_type, self.request_id, self.url, self._default_params, messages, extra_body)
        start_time = time.time()
        response = client.chat.completions.create(messages=messages, extra_body=extra_body, stream=False, **self._default_params)
        logger.info("#############Request {} LLMs Call INFO, request_id={}, processTime={}, response={}.",
                    self._llm_type, self.request_id, time.time() - start_time, response)
        return response.choices[0].message.content

    def _stream(
            self,
            prompt: str,
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
    ) -> Iterator[GenerationChunk]:
        """
        流式推理
        :return: 推理结果
        """
        api_key = random.choices(DEEPSEEK_API_KEY_POOL[0], DEEPSEEK_API_KEY_POOL[1], k=1)[0]
        client = OpenAI(api_key=api_key, base_url=self.url)
        messages = [
            {"role": "system", "content": self.system_role},
            {"role": "user", "content": prompt},
        ]
        if self.kwargs.get("enable_thinking"):
            extra_body = {"enable_thinking": True, "chat_template_kwargs": {"enable_thinking": True}}
        else:
            extra_body = {"enable_thinking": False, "chat_template_kwargs": {"enable_thinking": False}}
        logger.info("#############Request {} LLMs Stream INFO, request_id={}, url={}, params={}, message={}, extra_body={}.",
                    self._llm_type, self.request_id, self.url, self._default_params, messages, extra_body)
        start_time = time.time()
        stream = client.chat.completions.create(
            messages=messages,
            extra_body = extra_body,
            stream=True,
            **self._default_params,
        )
        response_usage = None
        response_content = ""
        for chunk in stream:
            if not chunk:
                continue
            response_usage = {
                "total_tokens": getattr(chunk.usage, 'total_tokens', 0),
                "input_tokens": getattr(chunk.usage, 'prompt_tokens', 0),
                "output_tokens": getattr(chunk.usage, 'completion_tokens', 0),
            } if chunk.choices[0].finish_reason == 'stop' else None
            response_content = response_content + chunk.choices[0].delta.content
            data = {"thinking": "", "content": chunk.choices[0].delta.content, "usage": response_usage}
            yield GenerationChunk(
                text=json.dumps(data),
                generation_info=data
            )
        logger.info("#############Request {} LLMs Stream INFO, request_id={}, processTime={}, content=[{}], usage={}.",
                    self._llm_type, self.request_id, time.time() - start_time, response_content, response_usage)

    def case_stream(
            self,
            prompt: str,
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
    ):
        """
        流式推理(本地调试)
        :return: 推理结果
        """
        for event in self._stream(prompt, stop, run_manager, **kwargs):
            print(event.text, end="")
            if event.generation_info:
                print(event.generation_info)
                pass


if __name__ == "__main__":
    # DeepseekAI().__call__(prompt="广州哪里好玩？")
    # DeepseekAI().case_stream(prompt="广州哪里好玩？")
    pass

