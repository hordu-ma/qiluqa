import random
import time
import uuid
from typing import Any, Mapping, List, Optional, Iterator, Type, AsyncIterator, Sequence, Union, Dict, Callable, Literal

from langchain_core.callbacks import CallbackManagerForLLMRun, AsyncCallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel, LanguageModelInput
from langchain_core.language_models.chat_models import generate_from_stream
from langchain_core.messages import BaseMessage, AIMessageChunk, BaseMessageChunk, HumanMessage, AIMessage, \
    SystemMessage
from langchain_core.outputs import ChatResult, ChatGenerationChunk
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool
from loguru import logger
from openai import OpenAI, AsyncOpenAI

from config.base_config_deepseek import DEEPSEEK_URL, DEEPSEEK_MODEL_NAME, DEEPSEEK_MAX_TOKENS, DEEPSEEK_TEMPERATURE, \
    DEEPSEEK_API_KEY_POOL
from models.chatai.convert_message import MessageChunkConverter


class ChatDeepseekAI(BaseChatModel):
    url: str = DEEPSEEK_URL
    llm_model_name: str = DEEPSEEK_MODEL_NAME
    max_tokens: int = int(DEEPSEEK_MAX_TOKENS)
    temperature: float = float(DEEPSEEK_TEMPERATURE)
    request_id: str = str(uuid.uuid4())
    streaming: bool = False
    history: List[List[str]] = None
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

    def _generate(self, messages: List[BaseMessage], stop: Optional[list[str]] = None,
                  run_manager: Optional[CallbackManagerForLLMRun] = None, **kwargs: Any) -> ChatResult:
        """
        常规推理
        :return: 推理结果
        """
        if self.streaming:
            stream_iter = self._stream(
                messages=messages, stop=stop, run_manager=run_manager, **kwargs
            )
            return generate_from_stream(stream_iter)
        logger.info("#############Request {} LLMs Generate INFO, request_id={}, url={}, params={}, message={}.",
                    self._llm_type, self.request_id, self.url, self._default_params, messages)
        start_time = time.time()
        messages = self._get_message_list(input_=messages)
        if self.kwargs.get("enable_thinking"):
            extra_body = {"enable_thinking": True, "chat_template_kwargs": {"enable_thinking": True}}
        else:
            extra_body = {"enable_thinking": False, "chat_template_kwargs": {"enable_thinking": False}}
        logger.info("#############Request {} LLMs Generate INFO, request_id={}, messages={}, extra_body={}.",
                    self._llm_type, self.request_id, messages, extra_body)
        api_key = random.choices(DEEPSEEK_API_KEY_POOL[0], DEEPSEEK_API_KEY_POOL[1], k=1)[0]
        client = OpenAI(api_key=api_key, base_url=self.url)
        response = client.chat.completions.create(messages=messages, extra_body=extra_body, stream=False, **self._default_params, **kwargs)
        logger.info("#############Response {} LLMs Generate INFO, request_id={}, processTime={}, response={}.",
                    self._llm_type, self.request_id, time.time() - start_time, response)
        generation_info = None
        return MessageChunkConverter.create_chat_result(response, generation_info)

    def _stream(
            self,
            messages: List[BaseMessage],
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """
        流式推理
        :return: 推理结果
         """
        logger.info("#############Request {} LLMs Stream INFO, request_id={}, url={}, params={}, message={}.",
                    self._llm_type, self.request_id, self.url, self._default_params, messages)
        start_time = time.time()
        messages = self._get_message_list(input_=messages)
        default_chunk_class: Type[BaseMessageChunk] = AIMessageChunk
        if self.kwargs.get("enable_thinking"):
            extra_body = {"enable_thinking": True, "chat_template_kwargs": {"enable_thinking": True}}
        else:
            extra_body = {"enable_thinking": False, "chat_template_kwargs": {"enable_thinking": False}}
        logger.info("#############Request {} LLMs Stream INFO, request_id={}, messages={}, extra_body={}.",
                    self._llm_type, self.request_id, messages, extra_body)
        api_key = random.choices(DEEPSEEK_API_KEY_POOL[0], DEEPSEEK_API_KEY_POOL[1], k=1)[0]
        client = OpenAI(api_key=api_key, base_url=self.url)
        response = client.chat.completions.create(messages=messages, extra_body=extra_body, stream=True, **self._default_params, **kwargs)
        logger.info("#############Response {} LLMs Stream INFO, request_id={}, processTime={}, response={}.",
                    self._llm_type, self.request_id, time.time() - start_time, response)
        base_generation_info = {}
        with response:
            is_first_chunk = True
            for chunk in response:
                logger.info("#############Response {} LLMs Stream INFO, request_id={}, processTime={}, chunk={}.",
                            self._llm_type, self.request_id, time.time() - start_time, chunk)
                if not isinstance(chunk, dict):
                    chunk = chunk.model_dump()
                generation_chunk = MessageChunkConverter.convert_chunk_to_generation_chunk(
                    chunk,
                    default_chunk_class,
                    base_generation_info if is_first_chunk else {},
                )
                if generation_chunk is None:
                    continue
                default_chunk_class = generation_chunk.message.__class__
                logprobs = (generation_chunk.generation_info or {}).get("logprobs")
                if run_manager:
                    run_manager.on_llm_new_token(
                        generation_chunk.text, chunk=generation_chunk, logprobs=logprobs
                    )
                is_first_chunk = False
                yield generation_chunk

    async def _astream(
            self,
            messages: List[BaseMessage],
            stop: Optional[List[str]] = None,
            run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
            **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        """
        异步流式推理
        :return: 推理结果
         """
        logger.info("#############Request {} LLMs AStream INFO, request_id={}, url={}, params={}, message={}.",
                    self._llm_type, self.request_id, self.url, self._default_params, messages)
        start_time = time.time()
        api_key = random.choices(DEEPSEEK_API_KEY_POOL[0], DEEPSEEK_API_KEY_POOL[1], k=1)[0]
        client = AsyncOpenAI(api_key=api_key, base_url=self.url)
        messages = self._get_message_list(input_=messages)
        default_chunk_class: Type[BaseMessageChunk] = AIMessageChunk
        base_generation_info = {}
        if self.kwargs.get("enable_thinking"):
            extra_body = {"enable_thinking": True, "chat_template_kwargs": {"enable_thinking": True}}
        else:
            extra_body = {"enable_thinking": False, "chat_template_kwargs": {"enable_thinking": False}}
        stream_options = {"include_usage": True}
        response = await client.chat.completions.create(messages=messages, stream=True, **self._default_params,
                                                        extra_body=extra_body, stream_options=stream_options, **kwargs)
        logger.info("#############Response {} LLMs AStream INFO, request_id={}, processTime={}, response={}.",
                    self._llm_type, self.request_id, time.time() - start_time, response)
        async with response:
            is_first_chunk = True
            async for chunk in response:
                if not isinstance(chunk, dict):
                    chunk = chunk.model_dump()
                generation_chunk = MessageChunkConverter.convert_chunk_to_generation_chunk(
                    chunk,
                    default_chunk_class,
                    base_generation_info if is_first_chunk else {},
                )
                if generation_chunk is None:
                    continue
                default_chunk_class = generation_chunk.message.__class__
                logprobs = (generation_chunk.generation_info or {}).get("logprobs")
                if run_manager:
                    await run_manager.on_llm_new_token(
                        generation_chunk.text, chunk=generation_chunk, logprobs=logprobs
                    )
                is_first_chunk = False
                yield generation_chunk

    def _get_message_list(self, input_: LanguageModelInput) -> list[dict]:
        """
        获取消息列表
        :return: 消息列表
        """
        messages_ = []
        messages = MessageChunkConverter.convert_input(input_).to_messages()
        for message in messages:
            if isinstance(message, SystemMessage):
                messages_.append(message)
                if self.history and len(self.history) > 0:
                    for h in self.history:
                        messages_.append(HumanMessage(content=h[0]))
                        messages_.append(AIMessage(content=h[1]))
            else:
                messages_.append(message)
        return [MessageChunkConverter.convert_message_to_dict(m) for m in messages_]

    def bind_tools(
            self,
            tools: Sequence[Union[Dict[str, Any], Type, Callable, BaseTool]],
            *,
            tool_choice: Optional[
                Union[dict, str, Literal["auto", "none", "required", "any"], bool]
            ] = None,
            strict: Optional[bool] = None,
            **kwargs: Any,
    ) -> Runnable[LanguageModelInput, BaseMessage]:
        """
        绑定工具
        :return: 绑定信息
        """
        formatted_tools = [
            convert_to_openai_tool(tool, strict=strict) for tool in tools
        ]
        if tool_choice:
            if isinstance(tool_choice, str):
                # tool_choice is a tool/function name
                if tool_choice not in ("auto", "none", "any", "required"):
                    tool_choice = {
                        "type": "function",
                        "function": {"name": tool_choice},
                    }
                if tool_choice == "any":
                    tool_choice = "required"
            elif isinstance(tool_choice, bool):
                tool_choice = "required"
            elif isinstance(tool_choice, dict):
                tool_names = [
                    formatted_tool["function"]["name"]
                    for formatted_tool in formatted_tools
                ]
                if not any(
                        tool_name == tool_choice["function"]["name"]
                        for tool_name in tool_names
                ):
                    raise ValueError(
                        f"Tool choice {tool_choice} was specified, but the only "
                        f"provided tools were {tool_names}."
                    )
            else:
                raise ValueError(
                    f"Unrecognized tool_choice type. Expected str, bool or dict. "
                    f"Received: {tool_choice}"
                )
            kwargs["tool_choice"] = tool_choice
        return super().bind(tools=formatted_tools, **kwargs)


if __name__ == "__main__":
    model = ChatDeepseekAI()
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful assistant. Answer all questions to the best of your ability.",
            ),
            ("user", "{input}"),
        ]
    )
    chain = prompt | model
    results = chain.invoke({"input": "hi"})
    for result in results:
        print(result)
