import json
from typing import Type, Optional, Dict, Mapping, Any, cast, Sequence, Union, List

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import BaseMessageChunk, HumanMessageChunk, AIMessageChunk, SystemMessageChunk, \
    FunctionMessageChunk, ChatMessageChunk, convert_to_messages, BaseMessage, ChatMessage, HumanMessage, AIMessage, \
    SystemMessage, FunctionMessage
from langchain_core.messages.ai import InputTokenDetails, UsageMetadata, OutputTokenDetails
from langchain_core.messages.tool import tool_call_chunk, ToolMessageChunk, ToolMessage, ToolCall, InvalidToolCall
from langchain_core.output_parsers.openai_tools import make_invalid_tool_call, parse_tool_call
from langchain_core.outputs import ChatGenerationChunk, ChatResult, ChatGeneration
from langchain_core.prompt_values import PromptValue, StringPromptValue, ChatPromptValue
import openai


class MessageChunkConverter:
    """消息块转换器"""

    class Constants:
        """LLM处理常量"""
        THINKING_INDICATOR: str = ""
        THINKING_CONTENT_PREFIX: str = ""

    @staticmethod
    def convert_chunk_to_generation_chunk(chunk: dict, default_chunk_class: Type[BaseMessageChunk],
                                          base_generation_info: Optional[Dict]
                                          ) -> Optional[ChatGenerationChunk]:
        token_usage = chunk.get("usage")
        choices = chunk.get("choices", [])
        usage_metadata: Optional[UsageMetadata] = (
            _create_usage_metadata(token_usage) if token_usage else None
        )
        # 处理空选择情况
        if len(choices) == 0:
            generation_chunk = ChatGenerationChunk(
                message=default_chunk_class(content="", usage_metadata=usage_metadata)
            )
            return generation_chunk

        choice = choices[0]
        # 提取思考内容
        reasoning_content = choice["delta"].get("reasoning_content")

        # 如果有思考内容，优先处理
        if reasoning_content:
            message_chunk = default_chunk_class(
                content=f"{MessageChunkConverter.Constants.THINKING_CONTENT_PREFIX}{reasoning_content}",
            )
            generation_info = {**base_generation_info} if base_generation_info else {}
            generation_info["is_thinking"] = True

            return ChatGenerationChunk(
                message=message_chunk,
                generation_info=generation_info
            )
        # 处理delta为空的情况additional_kwargs={"is_thinking"
        if choice["delta"] is None:
            return None

        message_chunk = _convert_delta_to_message_chunk(
            choice["delta"], default_chunk_class
        )
        generation_info = {**base_generation_info} if base_generation_info else {}
        if finish_reason := choice.get("finish_reason"):
            generation_info["finish_reason"] = finish_reason
            if model_name := chunk.get("model"):
                generation_info["model_name"] = model_name
            if system_fingerprint := chunk.get("system_fingerprint"):
                generation_info["system_fingerprint"] = system_fingerprint

        logprobs = choice.get("logprobs")
        if logprobs:
            generation_info["logprobs"] = logprobs

        if usage_metadata and isinstance(message_chunk, AIMessageChunk):
            message_chunk.usage_metadata = usage_metadata
        is_thinking = (
                not message_chunk.content and
                choice["delta"].get("reasoning_content") is not None and
                not finish_reason and
                not logprobs
        )
        if is_thinking:
            message_chunk.content = MessageChunkConverter.Constants.THINKING_INDICATOR
            generation_info["is_thinking"] = True
        else:
            generation_info["is_answer"] = True

        generation_chunk = ChatGenerationChunk(
            message=message_chunk, generation_info=generation_info or None
        )
        return generation_chunk

    @staticmethod
    def convert_input(input: LanguageModelInput) -> PromptValue:
        if isinstance(input, PromptValue):
            return input
        if isinstance(input, str):
            return StringPromptValue(text=input)
        if isinstance(input, Sequence):
            return ChatPromptValue(messages=convert_to_messages(input))
        msg = (
            f"Invalid input type {type(input)}. "
            "Must be a PromptValue, str, or list of BaseMessages."
        )
        raise ValueError(msg)

    @staticmethod
    def convert_message_to_dict(message: BaseMessage) -> dict:
        """Convert a LangChain message to a dictionary.

        Args:
            message: The LangChain message.

        Returns:
            The dictionary.
        """
        message_dict: Dict[str, Any] = {"content": _format_message_content(message.content)}
        if (name := message.name or message.additional_kwargs.get("name")) is not None:
            message_dict["name"] = name

        # populate role and additional message data
        if isinstance(message, ChatMessage):
            message_dict["role"] = message.role
        elif isinstance(message, HumanMessage):
            message_dict["role"] = "user"
        elif isinstance(message, AIMessage):
            message_dict["role"] = "assistant"
            if "function_call" in message.additional_kwargs:
                message_dict["function_call"] = message.additional_kwargs["function_call"]
            if message.tool_calls or message.invalid_tool_calls:
                message_dict["tool_calls"] = [
                                                 _lc_tool_call_to_openai_tool_call(tc) for tc in message.tool_calls
                                             ] + [
                                                 _lc_invalid_tool_call_to_openai_tool_call(tc)
                                                 for tc in message.invalid_tool_calls
                                             ]
            elif "tool_calls" in message.additional_kwargs:
                message_dict["tool_calls"] = message.additional_kwargs["tool_calls"]
                tool_call_supported_props = {"id", "type", "function"}
                message_dict["tool_calls"] = [
                    {k: v for k, v in tool_call.items() if k in tool_call_supported_props}
                    for tool_call in message_dict["tool_calls"]
                ]
            else:
                pass
            # If tool calls present, content null value should be None not empty string.
            if "function_call" in message_dict or "tool_calls" in message_dict:
                message_dict["content"] = message_dict["content"] or None

            if "audio" in message.additional_kwargs:
                # openai doesn't support passing the data back - only the id
                # https://platform.openai.com/docs/guides/audio/multi-turn-conversations
                raw_audio = message.additional_kwargs["audio"]
                audio = (
                    {"id": message.additional_kwargs["audio"]["id"]}
                    if "id" in raw_audio
                    else raw_audio
                )
                message_dict["audio"] = audio
        elif isinstance(message, SystemMessage):
            message_dict["role"] = message.additional_kwargs.get(
                "__openai_role__", "system"
            )
        elif isinstance(message, FunctionMessage):
            message_dict["role"] = "function"
        elif isinstance(message, ToolMessage):
            message_dict["role"] = "tool"
            message_dict["tool_call_id"] = message.tool_call_id

            supported_props = {"content", "role", "tool_call_id"}
            message_dict = {k: v for k, v in message_dict.items() if k in supported_props}
        else:
            raise TypeError(f"Got unknown type {message}")
        return message_dict

    @staticmethod
    def create_chat_result(
            response: Union[dict, openai.BaseModel],
            generation_info: Optional[Dict] = None,
    ) -> ChatResult:
        generations = []

        response_dict = (
            response if isinstance(response, dict) else response.model_dump()
        )
        if response_dict.get("error"):
            raise ValueError(response_dict.get("error"))

        token_usage = response_dict.get("usage")
        for res in response_dict["choices"]:
            message = _convert_dict_to_message(res["message"])
            if token_usage and isinstance(message, AIMessage):
                message.usage_metadata = _create_usage_metadata(token_usage)
            generation_info = generation_info or {}
            generation_info["finish_reason"] = (
                res.get("finish_reason")
                if res.get("finish_reason") is not None
                else generation_info.get("finish_reason")
            )
            if "logprobs" in res:
                generation_info["logprobs"] = res["logprobs"]
            gen = ChatGeneration(message=message, generation_info=generation_info)
            generations.append(gen)
        llm_output = {
            "token_usage": token_usage,
            "model_name": response_dict.get("model", ""),
            "system_fingerprint": response_dict.get("system_fingerprint", ""),
        }

        if isinstance(response, openai.BaseModel) and getattr(
                response, "choices", None
        ):
            message = response.choices[0].message  # type: ignore[attr-defined]
            if hasattr(message, "parsed"):
                generations[0].message.additional_kwargs["parsed"] = message.parsed
            if hasattr(message, "refusal"):
                generations[0].message.additional_kwargs["refusal"] = message.refusal

        return ChatResult(generations=generations, llm_output=llm_output)

def _lc_invalid_tool_call_to_openai_tool_call(
        invalid_tool_call: InvalidToolCall,
) -> dict:
    return {
        "type": "function",
        "id": invalid_tool_call["id"],
        "function": {
            "name": invalid_tool_call["name"],
            "arguments": invalid_tool_call["args"],
        },
    }


def _lc_tool_call_to_openai_tool_call(tool_call: ToolCall) -> dict:
    return {
        "type": "function",
        "id": tool_call["id"],
        "function": {
            "name": tool_call["name"],
            "arguments": json.dumps(tool_call["args"]),
        },
    }


def _format_message_content(content: Any) -> Any:
    """Format message content."""
    if content and isinstance(content, list):
        # Remove unexpected block types
        formatted_content = []
        for block in content:
            if (
                    isinstance(block, dict)
                    and "type" in block
                    and block["type"] == "tool_use"
            ):
                continue
            else:
                formatted_content.append(block)
    else:
        formatted_content = content

    return formatted_content


def _convert_delta_to_message_chunk(
        _dict: Mapping[str, Any], default_class: Type[BaseMessageChunk]
) -> BaseMessageChunk:
    id_ = _dict.get("id")
    role = cast(str, _dict.get("role"))
    content = cast(str, _dict.get("content") or "")
    additional_kwargs = {}
    if _dict.get("function_call"):
        function_call = dict(_dict["function_call"])
        if "name" in function_call and function_call["name"] is None:
            function_call["name"] = ""
        additional_kwargs["function_call"] = function_call
    tool_call_chunks = []
    if raw_tool_calls := _dict.get("tool_calls"):
        additional_kwargs["tool_calls"] = raw_tool_calls
        try:
            tool_call_chunks = [
                tool_call_chunk(
                    name=rtc["function"].get("name"),
                    args=rtc["function"].get("arguments"),
                    id=rtc.get("id"),
                    index=rtc["index"],
                )
                for rtc in raw_tool_calls
            ]
        except KeyError:
            pass

    if role == "user" or default_class == HumanMessageChunk:
        return HumanMessageChunk(content=content, id=id_)
    elif role == "assistant" or default_class == AIMessageChunk:
        return AIMessageChunk(
            content=content,
            additional_kwargs=additional_kwargs,
            id=id_,
            tool_call_chunks=tool_call_chunks,  # type: ignore[arg-type]
        )
    elif role in ("system", "developer") or default_class == SystemMessageChunk:
        if role == "developer":
            additional_kwargs = {"__openai_role__": "developer"}
        else:
            additional_kwargs = {}
        return SystemMessageChunk(
            content=content, id=id_, additional_kwargs=additional_kwargs
        )
    elif role == "function" or default_class == FunctionMessageChunk:
        return FunctionMessageChunk(content=content, name=_dict["name"], id=id_)
    elif role == "tool" or default_class == ToolMessageChunk:
        return ToolMessageChunk(
            content=content, tool_call_id=_dict["tool_call_id"], id=id_
        )
    elif role or default_class == ChatMessageChunk:
        return ChatMessageChunk(content=content, role=role, id=id_)
    else:
        return default_class(content=content, id=id_)


def _create_usage_metadata(oai_token_usage: dict) -> UsageMetadata:
    input_tokens = oai_token_usage.get("prompt_tokens", 0)
    output_tokens = oai_token_usage.get("completion_tokens", 0)
    total_tokens = oai_token_usage.get("total_tokens", input_tokens + output_tokens)
    input_token_details: dict = {
        "audio": (oai_token_usage.get("prompt_tokens_details") or {}).get(
            "audio_tokens"
        ),
        "cache_read": (oai_token_usage.get("prompt_tokens_details") or {}).get(
            "cached_tokens"
        ),
    }
    output_token_details: dict = {
        "audio": (oai_token_usage.get("completion_tokens_details") or {}).get(
            "audio_tokens"
        ),
        "reasoning": (oai_token_usage.get("completion_tokens_details") or {}).get(
            "reasoning_tokens"
        ),
    }
    return UsageMetadata(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        input_token_details=InputTokenDetails(
            **{k: v for k, v in input_token_details.items() if v is not None}
        ),
        output_token_details=OutputTokenDetails(
            **{k: v for k, v in output_token_details.items() if v is not None}
        ),
    )


def _convert_dict_to_message(_dict: Mapping[str, Any]) -> BaseMessage:
    """Convert a dictionary to a LangChain message.

    Args:
        _dict: The dictionary.

    Returns:
        The LangChain message.
    """
    role = _dict.get("role")
    name = _dict.get("name")
    id_ = _dict.get("id")
    if role == "user":
        return HumanMessage(content=_dict.get("content", ""), id=id_, name=name)
    elif role == "assistant":
        # Fix for azure
        # Also OpenAI returns None for tool invocations
        content = _dict.get("content", "") or ""
        additional_kwargs: Dict = {}
        if function_call := _dict.get("function_call"):
            additional_kwargs["function_call"] = dict(function_call)
        tool_calls = []
        invalid_tool_calls = []
        if raw_tool_calls := _dict.get("tool_calls"):
            additional_kwargs["tool_calls"] = raw_tool_calls
            for raw_tool_call in raw_tool_calls:
                try:
                    tool_calls.append(parse_tool_call(raw_tool_call, return_id=True))
                except Exception as e:
                    invalid_tool_calls.append(
                        make_invalid_tool_call(raw_tool_call, str(e))
                    )
        if audio := _dict.get("audio"):
            additional_kwargs["audio"] = audio
        return AIMessage(
            content=content,
            additional_kwargs=additional_kwargs,
            name=name,
            id=id_,
            tool_calls=tool_calls,
            invalid_tool_calls=invalid_tool_calls,
        )
    elif role in ("system", "developer"):
        if role == "developer":
            additional_kwargs = {"__openai_role__": role}
        else:
            additional_kwargs = {}
        return SystemMessage(
            content=_dict.get("content", ""),
            name=name,
            id=id_,
            additional_kwargs=additional_kwargs,
        )
    elif role == "function":
        return FunctionMessage(
            content=_dict.get("content", ""), name=cast(str, _dict.get("name")), id=id_
        )
    elif role == "tool":
        additional_kwargs = {}
        if "name" in _dict:
            additional_kwargs["name"] = _dict["name"]
        return ToolMessage(
            content=_dict.get("content", ""),
            tool_call_id=cast(str, _dict.get("tool_call_id")),
            additional_kwargs=additional_kwargs,
            name=name,
            id=id_,
        )
    else:
        return ChatMessage(content=_dict.get("content", ""), role=role, id=id_)
