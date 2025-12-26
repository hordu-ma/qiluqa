from pydantic import BaseModel, Field
from typing import Optional, Any


class QueryResponse(BaseModel):
    """
    接口返回结构体
    """
    status: Optional[int] = Field(
        default=0,
        title="status",
        description="响应状态",
    )
    message: str = Field(
        default=None,
        title="message",
        description="异常信息",
    )
    data: Any = Field(
        default=None,
        title="data",
        description="业务数据",
    )

