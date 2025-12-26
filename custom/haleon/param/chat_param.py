from typing import List

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
    bot_id: str = Field(
        default=None,
        title="bot_id",
        description="机器人标识",
    )
    user_id: str = Field(
        default=None,
        title="user_id",
        description="用户标识",
    )
    group_uuid: str = Field(
        default=None,
        title="group_uuid",
        description="会话分组标识",
    )
    use_mark: List[str] = Field(
        default=None,
        title="use_mark",
        description="用户标签",
    )
    answer_type: str = Field(
        default=None,
        title="answer_type",
        description="回答形式>>>\n简洁: 0 \n四段式: 1 \n追问: 2",
    )
    crowd_type: str = Field(
        default=None,
        title="crowd_type",
        description="沟通人群",
    )
    scene: str = Field(
        default=None,
        title="scene",
        description="场景值",
    )


class ChatParamExamples:
    """
    请求示例
    """
    examples = {
        "concise": {
            "summary": "简洁模式",
            "description": "简洁模式，answer_type必须传递0",
            "value": {
                "ques": "感觉自己很胖，应该如何减肥？",
                "bot_id": "038f5b6e90cb4a9c817bfba7a016d38b",
                "user_id": "100501",
                "group_uuid": "",
                "use_mark": [
                    "熬夜",
                    "运动少"
                ],
                "answer_type": "0",
                "crowd_type": "年龄45至60岁的女性",
                "scene": "RESEND"
            },
        },
        "four_stage": {
            "summary": "四段式模式",
            "description": "四段式模式，answer_type必须传递1",
            "value": {
                "ques": "感觉自己很胖，应该如何减肥？",
                "bot_id": "4ad4f6631b734700b448786e6c2dda1b",
                "user_id": "100501",
                "group_uuid": "",
                "use_mark": [
                    "熬夜",
                    "运动少"
                ],
                "answer_type": "1",
                "crowd_type": "年龄45至60岁的女性",
                "scene": "RESEND"
            },
        },
        "probe": {
            "summary": "追问",
            "description": "追问模式，answer_type必须传递2",
            "value": {
                "ques": "感觉自己很胖，应该如何减肥？",
                "bot_id": "7879c37db74440cfbc43e8fbedd9081a",
                "user_id": "100501",
                "group_uuid": "",
                "use_mark": [
                    "熬夜",
                    "运动少"
                ],
                "answer_type": "2",
                "crowd_type": "年龄45至60岁的女性",
                "scene": "RESEND"
            },
        }
    }
