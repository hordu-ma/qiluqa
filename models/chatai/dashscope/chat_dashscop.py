import time
import uuid
from typing import Optional, Any, Mapping, List, Iterator, Type, AsyncIterator, Dict, Sequence, Union, Callable, Literal

from langchain_core.callbacks import CallbackManagerForLLMRun, AsyncCallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel, LanguageModelInput
from langchain_core.language_models.chat_models import generate_from_stream
from langchain_core.messages import BaseMessage, BaseMessageChunk, AIMessageChunk, HumanMessage, AIMessage, \
    SystemMessage
from langchain_core.outputs import ChatResult, ChatGenerationChunk
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool
from loguru import logger
from openai import OpenAI, AsyncOpenAI

from config.base_config_dashscope import BASHSCOPE_MODEL_NAME, BASHSCOPE_MAX_TOKENS, BASHSCOPE_TEMPERATURE, \
    BASHSCOPE_BASE_URL, BASHSCOPE_API_KEY, BASHSCOPE_MODEL_TYPE, BASHSCOPE_VL_URL
from config.base_config_model_type import MODEL_TYPE_VL
from models.chatai.convert_message import MessageChunkConverter


class ChatDashScopeAI(BaseChatModel):
    """
       百炼聊天模型
           - 可提供普通对话
           - 可提供链式对话
    """
    base_url: str = BASHSCOPE_BASE_URL
    api_key: str = BASHSCOPE_API_KEY
    llm_model_name: str = BASHSCOPE_MODEL_NAME
    max_tokens: int = int(BASHSCOPE_MAX_TOKENS)
    temperature: float = float(BASHSCOPE_TEMPERATURE)
    history: List[List[str]] = None
    streaming: bool = False
    model_type: str = BASHSCOPE_MODEL_TYPE
    images: List[str] = []
    kwargs: dict[str, Any] = None
    request_id: str = str(uuid.uuid4())

    def __init__(self, *args: Any, **kwargs: Any):
        """
        构造函数
        :param args: 参数
        :param kwargs: 扩展参数
        """
        super().__init__(*args, **kwargs)
        self.kwargs = kwargs

        if kwargs.get("llm_model_name"):
            self.llm_model_name = kwargs.get("llm_model_name")

        if kwargs.get("base_url"):
            self.base_url = kwargs.get("base_url")

        if self.model_type == MODEL_TYPE_VL:
            self.base_url = BASHSCOPE_VL_URL

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
        start_time = time.time()
        messages = self._get_message_list(input_=messages)
        extra_body = {"enable_thinking": False, "chat_template_kwargs": {"enable_thinking": False}}
        logger.info("#############Request {} LLMs Generate INFO, request_id={}, url={}, params={}, message={}, extra_body={}.",
                    self._llm_type, self.request_id, self.base_url, self._default_params, messages, extra_body)
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        response = client.chat.completions.create(messages=messages, stream=False, **self._default_params,
                                                  extra_body=extra_body, **kwargs)
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
                    self._llm_type, self.request_id, self.base_url, self._default_params, messages)
        start_time = time.time()
        messages = self._get_message_list(input_=messages)
        default_chunk_class: Type[BaseMessageChunk] = AIMessageChunk
        if self.kwargs.get("enable_thinking"):
            extra_body = {"enable_thinking": True, "chat_template_kwargs": {"enable_thinking": True}}
        else:
            extra_body = {"enable_thinking": False, "chat_template_kwargs": {"enable_thinking": False}}
        stream_options = {"include_usage": True}
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        logger.info("#############Response {} LLMs Stream INFO, request_id={}, messages={}, extra_body={}.",
                    self._llm_type, self.request_id, messages, extra_body)
        response = client.chat.completions.create(messages=messages, stream=True, **self._default_params,
                                                  extra_body=extra_body, stream_options=stream_options, **kwargs)
        logger.info("#############Response {} LLMs Stream INFO, request_id={}, processTime={}, response={}.",
                    self._llm_type, self.request_id, time.time() - start_time, response)
        base_generation_info = {}
        with response:
            is_first_chunk = True
            for chunk in response:
                try:
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
                except Exception as e:
                    logger.error("#############Response LLMs Stream error, request_id={}, e={}", self.request_id, e)

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
        logger.info("#############Request LLMs AStream INFO, request_id={}, url={}, params={}, message={}.",
                    self._llm_type, self.request_id, self.base_url, self._default_params, messages)
        start_time = time.time()
        client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        messages = self._get_message_list(input_=messages)
        default_chunk_class: Type[BaseMessageChunk] = AIMessageChunk
        base_generation_info = {}
        if self.kwargs.get("enable_thinking"):
            extra_body = {"enable_thinking": True, "chat_template_kwargs": {"enable_thinking": True}}
        else:
            extra_body = {"enable_thinking": False, "chat_template_kwargs": {"enable_thinking": False}}
        stream_options = {"include_usage": True}
        logger.info("#############Response {} LLMs AStream INFO, request_id={}, messages={}, extra_body={}.",
                    self._llm_type, self.request_id, messages, extra_body)
        response = await client.chat.completions.create(messages=messages, stream=True, **self._default_params,
                                                        extra_body=extra_body, stream_options=stream_options, **kwargs)
        logger.info("#############Response {} LLMs AStream INFO, request_id={}, processTime={}, response={}.",
                    self._llm_type, self.request_id, time.time() - start_time, response)
        async with response:
            is_first_chunk = True
            async for chunk in response:
                try:
                    logger.info("#############Response {} LLMs AStream INFO, request_id={}, processTime={}, chunk={}.",
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
                        await run_manager.on_llm_new_token(
                            generation_chunk.text, chunk=generation_chunk, logprobs=logprobs
                        )
                    is_first_chunk = False
                    yield generation_chunk
                except Exception as e:
                    logger.error("#############Response {} LLMs AStream error, request_id={}, e={}", self.request_id, e)

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
            elif isinstance(message, HumanMessage) and self.model_type == MODEL_TYPE_VL and self.images and len(self.images) > 0:
                content = [{"type": "text", "text": message.content}]
                for image in self.images:
                    content.append({"type": "image_url", "image_url": {"url": image}})
                message.content = content
                messages_.append(message)
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
    # model = ChatDashScopeAI()
    model = ChatDashScopeAI(llm_model_name="qwen2.5-vl-32b-instruct", model_type=MODEL_TYPE_VL, images=["http://47.236.254.2/file/chat/20250512/a2c14e7ab0ef447e9ea50313904530ab.jpeg",
                                                              "https://dashscope.oss-cn-beijing.aliyuncs.com/images/tiger.png"])
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
    results = chain.stream({"input": "帮我识别图片"})
    for result in results:
        print(dict(result))
