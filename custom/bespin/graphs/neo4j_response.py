from pydantic import BaseModel, Field
from framework.api_model import QueryResponse
from framework.business_code import get_fastapi_model


class ChatResponseVO(BaseModel):
    """
    聊天问答业务返回
    """
    answer: str = Field(
        default="",
        title="answer",
        description="回答结果",
    )
    answer_list: list = Field(
        default=[],
        title="answer_list",
        description="回答结果",
    )


class ChatResponse(QueryResponse):
    """
    聊天问答返回结构体
    """
    data: ChatResponseVO = Field(
        default=None,
        title="data",
        description="业务数据",
    )


class ChatResponseExamples:
    examples = get_fastapi_model([])
