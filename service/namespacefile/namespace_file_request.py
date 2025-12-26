from typing import List
from pydantic import BaseModel, Field

from service.namespacefile.namespace_file_metadata import MetadataModel, MetadataImageModel


class MetadataImageParam(MetadataImageModel):
    """
    分片关联的图表信息
    """
    defList: List[str] = Field(
        default=[],
        title="defList",
        description="动态绑定信息",
    )


class MetadataParam(MetadataModel):
    images: List[MetadataImageParam] = Field(
        default=[],
        title="images",
        description="分片关联的图表信息",
    )


class ModifyChunkParam(BaseModel):
    uuid: str = Field(
        default="",
        title="uuid",
        description="唯一标识",
    )
    collectionId: str = Field(
        default="",
        title="collectionId",
        description="知识库标识",
    )
    customId: str = Field(
        default="",
        title="customId",
        description="分片标识",
    )
    document: str = Field(
        default="",
        title="document",
        description="分片明文信息",
    )
    fileId: str = Field(
        default="",
        title="fileId",
        description="文件标识",
    )
    namespace: str = Field(
        default="",
        title="namespace",
        description="知识库命名空间",
    )
    metadata: MetadataParam = Field(
        default="",
        title="metadata",
        description="知识库元数据信息"
    )
    chunkLabel: str = Field(
        default="",
        title="chunk_label",
        description="分片标签信息"
    )


class ModifyChunkParamExamples:
    """
    请求示例
    """
    examples = {
        "default": {
            "summary": "默认场景",
            "description": "默认场景下的分片编辑",
            "value": {

            },
        },
    }


class ChunkPageParam(BaseModel):
    """
    查询知识文件的分片列表
    """
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
    content: str = Field(
        default="",
        title="content",
        description="分片内容",
    )
    file_id: str = Field(
        default="",
        title="file_id",
        description="文件标识",
    )
    ids: List[str] = Field(
        default=[],
        title="ids",
        description="分片标识列表",
    )
    status: str = Field(
        default="",
        title="status",
        description="分片状态(开启或禁用)"
    )


class ChunkPageParamExamples:
    """
    查询知识文件的分片列表 - 请求示例
    """
    examples = {
        "default": {
            "summary": "默认场景",
            "description": "默认场景下的分页查询",
            "value": {
                "page_nums": "1",
                "page_size": "10",
                "content": "100501",
                "file_id": "50002",
                "status": "",
                "ids": []
            },
        },
    }


class ChunkFileStatusParam(BaseModel):
    """
    通过文件ID修改分片状态请求示例
    """
    file_id_list: list[str] = Field(
        default=[],
        title="file_id_list",
        description="文件ID列表",
    )
    status_tag: str = Field(
        default=1,
        title="tag",
        description="修改状态类型",
    )


class ChunkFileStatusParamExamples:
    """
    通过文件ID修改分片状态--请求示例
    """
    examples = {
        "default": {
            "summary": "默认场景",
            "description": "默认场景下的文件分片状态编辑",
            "value": {

            },
        },
    }


class DelFileParam(BaseModel):
    """
    通过文件ID修改分片状态请求示例
    """
    namespace: str = Field(
        default="",
        title="namespace",
        description="知识库信息",
    )
    file_id_list: list[str] = Field(
        default=[],
        title="file_id_list",
        description="文件ID列表",
    )


class DelFileParamExamples:
    """
    通过文件ID删除分片状态--请求示例
    """
    examples = {
        "default": {
            "summary": "默认场景",
            "description": "默认场景下的删除相关文件知识库分片信息",
            "value": {

            },
        },
    }


class DelChunkParam(BaseModel):
    """
    删除分片信息请求示例
    """
    namespace_id: str = Field(
        default="",
        title="namespace_id",
        description="知识库信息ID",
    )
    file_id: str = Field(
        default="",
        title="file_id",
        description="文件ID",
    )
    ids: list[str] = Field(
        default=[],
        title="ids",
        description="分片ID",
    )
    is_want_deleted_file: bool = Field(
        default=False,
        title="is_want_deleted_file",
        description="是要删除整个文件",
    )
    is_null_deleted_file: bool = Field(
        default=True,
        title="is_null_deleted_file",
        description="分片为空时默认是否删除文件",
    )


class DelChunkParamExamples:
    """
       删除分片状态--请求示例
    """
    examples = {
        "default": {
            "summary": "默认场景",
            "description": "默认场景下的删除知识库分片信息",
            "value": {

            },
        },
    }


class ChunkStatusParam(BaseModel):
    """
    通过分片ID修改分片状态请求示例
    """
    custom_id_list: list[str] = Field(
        default=[],
        title="file_id_list",
        description="分片ID列表",
    )
    status_tag: str = Field(
        default=1,
        title="tag",
        description="修改状态类型",
    )


class DelFileVectorParam(BaseModel):
    """
    通过文件ID删除分片片--请求示例
    """
    file_id_list: list[str] = Field(
        default=[],
        title="file_id_list",
        description="文件列表",
    )
    namespace: str = Field(
        default="",
        title="namespace",
        description="知识库名称",
    )


class ChunkStatusParamExamples:
    """
    通过文件ID修改分片状态--请求示例
    """
    examples = {
        "default": {
            "summary": "默认场景",
            "description": "默认场景下的分片状态编辑",
            "value": {

            },
        },
    }


class DelFileVectorParamExamples:
    """
    通过文件ID删除分片--请求示例
    """
    examples = {
        "default": {
            "summary": "默认场景",
            "description": "默认场景下的分片状态编辑",
            "value": {

            },
        },
    }


class SpiderUrlParam(BaseModel):
    """
    爬取网站信息
    """
    namespace: str = Field(
        default="",
        title="namespace",
        description="知识库名称",
    )
    url: str = Field(
        default="",
        title="url",
        description="网站链接",
    )
    namespace_id: str = Field(
        default="",
        title="namespaceId",
        description="知识库ID信息"
    )
    url_id: str = Field(
        default="",
        title="urlId",
        description="网站ID信息"
    )
    file_id: str = Field(
        default="",
        title="fileId",
        description="爬虫网站信息ID"
    )


class SpiderUrlParamExamples:
    """
    通过Url爬取网站信息--请求示例
    """
    examples = {
        "default": {
            "summary": "默认场景",
            "description": "默认场景下的分片状态编辑",
            "value": {
                        "url": "",
                        "namespace_id": "",
                        "url_id": "",
                        "file_id": ""
                    },
        },
    }
