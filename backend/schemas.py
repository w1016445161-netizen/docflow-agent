"""Pydantic 序列化 Schema。

用于 API 响应的数据序列化和类型校验。
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentOut(BaseModel):
    """文档状态/元数据响应模型。"""

    doc_id: str
    filename: str
    file_type: str
    status: str
    parse_method: str
    char_count: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentListOut(BaseModel):
    """文档列表响应模型。"""

    documents: list[DocumentOut]


class QARecordOut(BaseModel):
    """问答记录响应模型。"""

    id: int
    document_id: str
    question: str
    answer: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentStatusOut(BaseModel):
    """文档状态查询响应。"""

    doc_id: str
    filename: str
    status: str
    parse_method: str
    char_count: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
