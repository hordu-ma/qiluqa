import json
import time
import uuid
from random import randint
from typing import Any, List, Optional, Iterator, Mapping

import requests
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
from langchain_core.outputs import GenerationChunk
from loguru import logger
from openai import OpenAI

from config.base_config import DEFAULT_CHAT_BOT_ROLE
from config.base_config_dashscope import *
from config.base_config_model_type import MODEL_TYPE_VL


class DashScopeAI(LLM):
    base_url: str = BASHSCOPE_BASE_URL
    http_url: str = BASHSCOPE_HTTP_URL
    multimodal_http_url: str = BASHSCOPE_MULTIMODAL_HTTP_URL
    api_key: str = BASHSCOPE_API_KEY
    llm_model_name: str = BASHSCOPE_MODEL_NAME
    max_tokens: int = int(BASHSCOPE_MAX_TOKENS)
    temperature: float = float(BASHSCOPE_TEMPERATURE)
    top_p: float = float(BASHSCOPE_TOP_P)
    top_k: int = int(BASHSCOPE_TOP_K)
    want_resend: float = float(BASHSCOPE_WANT_RESEND)
    request_id: str = str(uuid.uuid4())
    system_role: str = DEFAULT_CHAT_BOT_ROLE
    history: List[List[str]] = None
    model_type: str = BASHSCOPE_MODEL_TYPE
    images: List[str] = None
    kwargs: dict[str, Any] = None
    tools: List[Any] = None

    def __init__(self, *args: Any, **kwargs: Any):
        """
        构造函数
        :param args: 参数
        :param kwargs: 扩展参数
        """
        super().__init__(*args, **kwargs)
        self.tools = []
        self.kwargs = kwargs
        if self.model_type == MODEL_TYPE_VL:
            self.base_url = BASHSCOPE_VL_URL

    def bind_tools(self, tools: List[Any]) -> "DashScopeAI":
        """实现bind_tools方法，支持工具调用"""
        # 记录可用工具
        self.tools = tools
        return self

    @property
    def _llm_type(self) -> str:
        return "Dashscope"

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
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        messages = self._get_message_list(prompt=prompt)
        logger.info("#############Request {} LLMs Call INFO, request_id={}, url={}, params={}, message={}.",
                    self._llm_type, self.request_id, self.base_url, self._default_params, messages)
        start_time = time.time()
        extra_body = {"enable_thinking": False, "chat_template_kwargs": {"enable_thinking": False}}
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
        headers = {
            "Content-Type": "application/json",
            'X-DashScope-SSE': 'enable',
            "Authorization": "Bearer " + self.api_key,
        }
        messages = self._get_message_list(prompt=prompt)
        request_json = {
            "model": self.llm_model_name,
            "input": {
                "messages": messages,
            },
            "parameters": {
                "top_p": self.top_p,
                "top_k": self.top_k,
                "temperature": self.temperature,
                "seed": 1234 if not self.want_resend else randint(BASHSCOPE_SEND_MIN, BASHSCOPE_SEND_MAX),
                'incremental_output': True,
                "enable_thinking": False,
                "enable_search": False,
                "result_format": "message",
                "stream": True,
                "stream_options": {
                    "include_usage": True
                }
            },
        }
        # http_url兼容VL模型
        url = self.multimodal_http_url if self.model_type == MODEL_TYPE_VL and self.images and len(self.images) > 0 else self.http_url
        # 深度思考过程参数设置
        if self.kwargs.get("enable_thinking"):
            request_json["parameters"]["enable_thinking"] = True
            request_json["parameters"]["thinking_budget"] = self.kwargs.get("thinking_budget")
        logger.info("#############Request {} LLMs Stream INFO, request_id={}, url={}, headers={}, json={}.",
                    self._llm_type, self.request_id, url, headers, request_json)
        start_time = time.time()
        response = requests.post(url=url, headers=headers, json=request_json, stream=True)
        response_usage = None
        response_content = ""
        reasoning_content = ""
        for chunk in response.iter_lines(chunk_size=1024, decode_unicode=True):
            logger.info("#############chunk={}.", chunk)
            if not chunk or "data:" not in str(chunk):
                continue
            response_data = json.loads(chunk.split("data:")[1])
            output = response_data.get("output", None)
            if not output:
                continue
            choices = output.get("choices", None)
            if not choices:
                continue
            # token信息
            if response_data.get("usage") and choices[0].get("finish_reason") == "stop":
                response_usage = {
                    "input_tokens": response_data["usage"].get("input_tokens", 0),
                    "output_tokens": response_data["usage"].get("output_tokens", 0),
                    "total_tokens": response_data["usage"].get("total_tokens", 0)
                }
            data = None
            if response_usage is not None:
                data = {"thinking": "", "content": "", "usage": response_usage}
            message = choices[0].get("message")
            if message is not None:
                # 思考过程
                reasoning = message.get("reasoning_content", "")
                reasoning_content += reasoning
                # 回复内容信息
                # 返回结果兼容VL模型
                if self.model_type == MODEL_TYPE_VL and self.images and len(self.images) > 0:
                    content = message.get("content")[0].get("text", "") if message.get("content") and len(message.get("content")) > 0 else ""
                else:
                    content = message.get("content", "")
                response_content += content
                data = {"thinking": reasoning, "content": content, "usage": response_usage}
            yield GenerationChunk(
                text=json.dumps(data, ensure_ascii=False, indent=4),
                generation_info=data
            )
            logger.info("#############Request {} LLMs Stream INFO, request_id={}, processTime={}, content=[{}], "
                        "usage={},reasoning={}.", self._llm_type, self.request_id, time.time() - start_time,
                        response_content, response_usage, reasoning_content, )

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
            logger.info("text:{}", event.text)
            if event.generation_info:
                logger.info("generation_info:{}", event.generation_info)
                pass

    def _get_message_list(self, prompt: str) -> list[dict]:
        messages = [
            {"role": "system", "content": self.system_role}
        ]
        if self.history and len(self.history) > 0:
            for h in self.history:
                messages.append({
                    "role": "user",
                    "content": h[0],
                })
                messages.append({
                    "role": "assistant",
                    "content": h[1],
                })
        # 入参兼容VL模型
        if self.model_type == MODEL_TYPE_VL and self.images and len(self.images) > 0:
            content = []
            for image in self.images:
                content.append({"image": image})
            content.append({"text": prompt})
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "user", "content": prompt})
        return messages


if __name__ == "__main__":
    params = {
        "enable_search": True,
        "enable_thinking": False
    }
    dashScopeAI = DashScopeAI(**params, model_type=MODEL_TYPE_VL, images=["http://47.236.254.2/file/chat/20250512/a2c14e7ab0ef447e9ea50313904530ab.jpeg","https://dashscope.oss-cn-beijing.aliyuncs.com/images/tiger.png"])
    DashScopeAI()._call(prompt="广州哪里好玩？")
    # dashScopeAI.case_stream(prompt="推荐图片中类似的旅游胜地给我？")
