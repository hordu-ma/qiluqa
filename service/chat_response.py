from typing import List
from pydantic import BaseModel, Field
from framework.api_model import QueryResponse
from framework.business_code import get_fastapi_model, ERROR_10000, ERROR_10001, ERROR_10007, ERROR_10008


class ChatSlaveResultResponseVO(BaseModel):
    """
    从节点机器人调度结果
    """
    bot_id: str = Field(
        default=None,
        title="bot_id",
        description="从节点机器人业务标识",
    )
    field: str = Field(
        default=None,
        title="field",
        description="从节点机器人业务字段",
    )
    answer: str = Field(
        default=[],
        title="answer",
        description="从节点机器人问答结果",
    )


class ChatMetadataImagesResponseVO(BaseModel):
    """
    分片关联的图表信息
    """
    name: str = Field(
        default=None,
        title="name",
        description="图表名称",
    )
    path: str = Field(
        default=None,
        title="path",
        description="图表路径",
    )
    mark_num: str = Field(
        default=None,
        title="mark_num",
        description="图表序号",
    )
    page_num: str = Field(
        default=None,
        title="page_num",
        description="图表页码",
    )
    excel_id: str = Field(
        default=None,
        title="excel_id",
        description="所属文件业务标识",
    )
    image_id: str = Field(
        default=None,
        title="image_id",
        description="图表业务标识",
    )


class ChatMetadataResponseVO(BaseModel):
    """
    召回的分片元数据
    """
    name: str = Field(
        default=None,
        title="name",
        description="分片所属源文件名称",
    )
    score: float = Field(
        default=None,
        title="score",
        description="匹配度",
    )
    content: str = Field(
        default=None,
        title="content",
        description="明文信息",
    )
    source: str = Field(
        default=None,
        title="source",
        description="分片所属源文件目录地址",
    )
    images: List[ChatMetadataImagesResponseVO] = Field(
        default=[],
        title="images",
        description="分片关联的图表列表",
    )


class ChatResponseVO(BaseModel):
    """
    聊天问答业务返回
    """
    answer: str = Field(
        default=None,
        title="answer",
        description="回答结果",
    )

    thinking: str = Field(
        default=None,
        title="thinking",
        description="思考过程",
    )

    search: List[dict] = Field(
        default=None,
        title="search",
        description="搜索结果",
    )

    history_id: int = Field(
        default=0,
        title="history_id",
        description="历史聊天记录标识",
    )
    scene: str | None = Field(
        default=None,
        title="scene",
        description="当前业务场景值",
    )
    metadata: List[ChatMetadataResponseVO] = Field(
        default=[],
        title="metadata",
        description="召回的分片元数据",
    )
    slave_result: List[ChatSlaveResultResponseVO] = Field(
        default=[],
        title="slave_result",
        description="从节点机器人调度结果",
    )
    answer_list: List[str] = Field(
        default=[],
        title="answer_list",
        description="追问场景问答列表",
    )
    label_list: List[str] = Field(
        default=[],
        title="label_list",
        description="表格标签列表"
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

    class Config:
        json_schema_extra = {
            "example": {
                "status": 0,
                "message": "",
                "data": {
                    "answer": "对于您这个年龄段的女性，减肥重点在于合理饮食与适度运动相结合。建议保证每天蔬菜水果摄入充足，控制热量密集食物，"
                              "比如糖分高、油脂大的食品。可以选择更多的低脂肪、高蛋白食物，并确保膳食纤维的摄入。结合您的运动情况，可以适当增加有氧运动的时间和频率，"
                              "比如慢跑和游泳，帮助燃烧脂肪。同时，不要忽视抗阻运动，它有助于增加肌肉，提升基础代谢率，让身体在静息状态下也能更多地消耗热量。记得调整作息，"
                              "避免熬夜，因为熬夜可能影响代谢，不利于减肥。请记住，减肥是一个持久的过程，关键在于找到适合自己的生活方式并持之以恒。"
                              "\n<a href='/content/ECL14540383896997888膳食推荐摄入[1-1].png' target='_blank'>表1-1</a>"
                              "\n<a href='/content/ECL14540383896997888运动建议和计划[1-14].png' target='_blank'>表1-14</a>"
                              "\n\n建议参考了《中国居民膳食指南（2022） (中国营养学会) (z-lib.org) (1)上》",
                    "history_id": 1457,
                    "scene": "",
                    "metadata": [
                        {
                            "name": "中国居民膳食指南（2022） (中国营养学会) (z-lib.org) (1)上.docx",
                            "source": "/app/bespin-local-qa/content/中国居民膳食指南2022.docx",
                            "images": [{
                                "name": "ECL14540383896997888膳食推荐摄入[1-1].png",
                                "path": "/app/bespin-local-qa/content/ECL14540383896997888膳食推荐摄入[1-1].png",
                                "mark_num": "1-1",
                                "page_num": "4",
                                "excel_id": "ECL14540383896997888",
                                "image_id": "IMAGE14540383897653248"
                            },
                                {
                                    "name": "ECL14540383896997888运动建议和计划[1-14].png",
                                    "path": "/app/bespin-local-qa/content/ECL14540383896997888运动建议和计划[1-14].png",
                                    "mark_num": "1-14",
                                    "page_num": "28",
                                    "excel_id": "ECL14540383896997888",
                                    "image_id": "IMAGE14540384023351296"
                                }
                            ]
                        }
                    ],
                    "slave_result": [{
                        "bot_id": "854052fff28c4768ab02299c87e29d2a",
                        "field": "idea",
                        "answer": "对于45至60岁的女性来说，减轻体重应当注重综合方法。首先，在饮食方面，建议均衡摄取各类营养，适量减少高糖、高脂肪食品，多吃蔬菜、水果和粗粮，保证每日蛋白质摄入，控制总热量在适宜范围内。其次，鉴于您已有的运动习惯，可以增加抗阻运动的频率和强度，帮助提升代谢率和增加肌肉量，这对于燃烧脂肪和塑形很有帮助。同时，确保每次运动后都有足够的拉伸来缓解肌肉紧张。最后，尽量避免久坐，每小时起身活动，日常生活中尽可能多走路。记住，健康的减肥是持久的过程，既要合理调整生活习惯，也要注意心态平和，不要过度追求短期效果。"
                    },
                        {
                            "bot_id": "50978f83ff14478c8b0bcceaccfe2fd1",
                            "field": "solace",
                            "answer": "亲爱的女士，虽然这段时间您可能感觉有些疲惫，毕竟生活中的忙碌和缺少休息都让您身体有些吃不消。但是请相信，您坚韧的内心比您想象得更为强大。多关注自己，尝试在日常生活中挤出一些时间来享受宁静的夜晚，增加适量的运动会让您的身心焕发新的活力。请您坚信，明天的阳光正为您而照耀，美好的改变就在坚持与调整之间悄然发生。"
                        },
                        {
                            "bot_id": "",
                            "field": "trace",
                            "answer": "建议参考了《中国居民膳食指南（2022） (中国营养学会) (z-lib.org) (1)上》，必要情况建议咨询医生，希望对您有所帮助。"
                        }],
                    "answer_list": [
                        "如亲需要更详细的营养建议，这边还需要您提供更进一步的信息：",
                        "您当前的身高、体重以及饮食习惯是怎样的？每日三餐是否均衡且定时定量？",
                        "您在熬夜后是否会补偿性地多吃或者选择高热量食物？平时的晚餐时间和夜宵习惯如何？",
                        "考虑到您的运动量已相当不错，但仍有减重需求，是否在运动后补充了过多的蛋白质或能量饮料？您是否了解并遵循了“吃动平衡”的原则？"
                    ],
                    "label_list": [

                    ]
                }
            }
        }


class ChatResponseExamples:
    examples = get_fastapi_model([ERROR_10000, ERROR_10001, ERROR_10007, ERROR_10008])
