import json
import time
import uuid
from typing import Any, List, Optional, Iterator, Mapping
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
from langchain_core.outputs import GenerationChunk
from loguru import logger
from openai import OpenAI

from config.base_config import DEFAULT_CHAT_BOT_ROLE
from config.base_config_openai import *


class ChatOpenAI(LLM):

    api_key: str = BASE_OPENAI_API_KEY
    llm_model_name: str = BASE_OPENAI_MODEL_NAME
    max_tokens: int = int(BASE_OPENAI_OUTPUT_TOKEN_LENGTH)
    temperature: float = float(BASE_OPENAI_TEMPERATURE)
    request_id: str = str(uuid.uuid4())
    system_role: str = DEFAULT_CHAT_BOT_ROLE

    @property
    def _llm_type(self) -> str:
        return "OpenAI"

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
        client = OpenAI(api_key=self.api_key)
        messages = [
            {"role": "system", "content": self.system_role},
            {"role": "user", "content": prompt},
        ]
        logger.info("#############Request {} LLMs Call INFO, request_id={}, url={}, params={}, message={}.",
                    self._llm_type, self.request_id, "https://api.openai.com/v1", self._default_params, messages)
        start_time = time.time()
        response = client.chat.completions.create(messages=messages, stream=False, **self._default_params)
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
        client = OpenAI(api_key=self.api_key)
        messages = [
            {"role": "system", "content": self.system_role},
            {"role": "user", "content": prompt},
        ]
        logger.info("#############Request {} LLMs Call INFO, request_id={}, url={}, params={}, message={}.",
                    self._llm_type, self.request_id, "https://api.openai.com/v1", self._default_params, messages)
        start_time = time.time()
        stream = client.chat.completions.create(
            messages=messages,
            stream=True,
            stream_options={"include_usage": True},
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
            } if chunk.usage else None

            choices0_content = chunk.choices[0].delta.content if chunk.choices and chunk.choices[0].delta.content else ""
            response_content = response_content + choices0_content

            yield GenerationChunk(
                text=choices0_content,
                generation_info=response_usage,
            )
            if response_usage:
                yield GenerationChunk(
                    text=json.dumps(response_usage),
                    generation_info=response_usage
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
    # ChatOpenAI().__call__(prompt="广州哪里好玩？")
    # ChatOpenAI().case_stream(prompt="广州哪里好玩？")
    pass

