from typing import List
from pydantic import BaseModel, Field


class MetadataImageModel(BaseModel):
    """
    分片关联的图表信息
    """
    image_id: str = Field(
        default=None,
        title="image_id",
        description="图表业务标识",
    )


class MetadataModel(BaseModel):
    source: str = Field(
        default="",
        title="source",
        description="源文件信息",
    )
    answer: str = Field(
        default="",
        title="answer",
        description="标准回答",
    )
    scene: str = Field(
        default="",
        title="scene",
        description="场景值",
    )
    name: str = Field(
        default="",
        title="name",
        description="源文件名称",
    )
    images: List[str] = Field(
        default=[],
        title="images",
        description="分片关联的图表信息",
    )
    chunk_label: str = Field(
        default="",
        title="chunk_label",
        description="分片标签"
    )

    def default_serializer(self):
        if isinstance(self, MetadataModel):
            return {
                'source': self.source,
                'answer': self.answer,
                'scene': self.scene,
                'name': self.name,
                'images': self.images,
                'chunk_label': self.chunk_label
            }
        raise TypeError("Not serializable")
