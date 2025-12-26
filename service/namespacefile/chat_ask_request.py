# 定义文件信息模型
from typing import Optional, List

from pydantic import BaseModel


class ChatFileInfo(BaseModel):
    filePath: str
    fileName: str
    fileType: str
    preprocessedFilePath: str
    fileSize: int

# 定义请求模型
class ChatRequest(BaseModel):
    files: Optional[List[ChatFileInfo]] = None