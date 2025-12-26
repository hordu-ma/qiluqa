from datetime import datetime
from typing import List

from pydantic import Field, BaseModel

from framework.api_model import QueryResponse
from framework.business_code import get_fastapi_model, ERROR_10001, ERROR_10210, ERROR_10207


class ChunkPageEmbeddingResponseVO(BaseModel):
    """
    查询知识文件的分片列表 - 业务返回
    """
    uuid: str = Field(
        default="",
        title="uuid",
        description="唯一标识",
    )
    collection_id: str = Field(
        default="",
        title="collection_id",
        description="知识库标识",
    )
    custom_id: str = Field(
        default="",
        title="custom_id",
        description="分片标识",
    )
    document: str = Field(
        default="",
        title="document",
        description="分片明文信息",
    )
    metadata: dict = Field(
        default=None,
        title="metadata",
        description="分片元信息",
    )
    file_id: str = Field(
        default="",
        title="file_id",
        description="文件标识",
    )
    create_date: datetime = Field(
        default="",
        title="create_date",
        description="创建时间",
    )
    update_date: datetime = Field(
        default="",
        title="update_date",
        description="更新时间",
    )
    number: str = Field(
        default="",
        title="number",
        description="序号"
    )
    status: str = Field(
        default="",
        title="status",
        description="分片状态"
    )
    document_len: int = Field(
        default="",
        title="document_len",
        description="分片字符长度"
    )
    chunk_label: str = Field(
        default="",
        title="chunk_label",
        description="分片标签"
    )


class ChunkPageResponseVO(BaseModel):
    """
    查询知识文件的分片列表 - 业务返回
    """
    page_total: str = Field(
        default=0,
        title="page_total",
        description="分片总数",
    )
    page_nums: str = Field(
        default=1,
        title="page_nums",
        description="分页页码",
    )
    page_size: str = Field(
        default=10,
        title="page_size",
        description="分页条数",
    )
    chunk_list: List[ChunkPageEmbeddingResponseVO] = Field(
        default=[],
        title="chunk_list",
        description="分片数据",
    )


class ChunkPageResponse(QueryResponse):
    """
    查询知识文件的分片列表 - 返回结构体
    """
    data: ChunkPageResponseVO = Field(
        default=None,
        title="data",
        description="业务数据",
    )


class ChunkPageResponseExamples:
    examples = get_fastapi_model([ERROR_10001, ERROR_10207, ERROR_10210])
