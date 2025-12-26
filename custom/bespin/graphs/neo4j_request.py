from pydantic import BaseModel, Field


class ChatParam(BaseModel):
    """
    请求参数
    """
    ques: str = Field(
        default=None,
        title="ques",
        description="问题",
    )

    is_direct_return: bool = Field(
        default=False,
        title="ques",
        description="是否直接返回结果",
    )

    is_middle_return: bool = Field(
        default=False,
        title="ques",
        description="是否返回中间结果",
    )


class ChatParamExamples:
    """
    请求示例
    """
    examples = {
        "normal": {
            "summary": "普通模式",
            "description": "普通模式",
            "value": {
                "ques": "感觉自己很胖，应该如何减肥？",
            },
        }
    }
