from pydantic import BaseModel, Field


class InferParam(BaseModel):
    chat_images_id: str = Field(
        default=None,
        title="chat_images_id",
        description="图片生成请求标识",
    )


class FcInferParam(BaseModel):
    style: str = Field(
        default=None,
        title="style",
        description="风格",
    )
    person_name: str = Field(
        default=None,
        title="person_name",
        description="推理所需使用的人物名称",
    )
    num_generate: int = Field(
        default=1,
        title="num_generate",
        description="推理生成的图片数量",
    )
