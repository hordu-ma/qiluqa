from pydantic import BaseModel, Field


class UploadExcelParam(BaseModel):
    """
    上传图表文件
    """
    path: str = Field(
        default="",
        title="path",
        description="挂载目录",
    )
    file_type: str = Field(
        default="",
        title="file_type",
        description="文件类型",
    )
    file_path: str = Field(
        default="",
        title="file_path",
        description="文件目录",
    )
    file_name: str = Field(
        default="",
        title="file_name",
        description="文件名称",
    )
    file_size: str = Field(
        default="",
        title="file_size",
        description="文件大小",
    )
    namespace_id: str = Field(
        default="",
        title="namespace_id",
        description="知识库标识",
    )
    file_id: str = Field(
        default="",
        title="file_id",
        description="文件标识",
    )


class UploadExcelParamExamples:
    """
    上传图表文件 - 请求示例
    """
    examples = {
        "default": {
            "summary": "默认场景",
            "description": "上传图表文件",
            "value": {
                "ids": []
            },
        },
    }
