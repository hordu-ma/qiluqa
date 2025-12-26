import uuid
from typing import List
from pydantic import BaseModel, Field


class TrainParam(BaseModel):
    chat_images_id: str = Field(
        default=None,
        title="chat_images_id",
        description="图片生成请求标识",
    )


class FcTrainParam(BaseModel):
    img64_list: List[str] = Field(
        default=[],
        title="img64_list",
        description="图片序列列表",
    )
    person_name: str = Field(
        default=uuid.uuid4(),
        title="person_name",
        description="推理所需使用的人物名称",
    )
