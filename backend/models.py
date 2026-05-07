"""SQLAlchemy ORM 模型。

包含 DocumentStatus 枚举、Document 表、QARecord 表。
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text

from backend.database import Base


class DocumentStatus(str, enum.Enum):
    """文档处理状态枚举。

    流转：uploaded → parsing → parsed → summarizing → ready
    任何节点异常 → failed
    """

    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    SUMMARIZING = "summarizing"
    READY = "ready"
    FAILED = "failed"


class Document(Base):
    """文档元数据表。

    记录的文件存储于 storage/uploads/，chunk 索引仍沿用 JSON 文件。
    """

    __tablename__ = "documents"

    id = Column(String(36), primary_key=True)  # 对应 doc_id UUID
    filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # txt/pdf/docx/xlsx/md
    storage_path = Column(String(512), nullable=False)
    parse_method = Column(String(20), default="unknown")  # text/ocr/excel/unknown
    char_count = Column(Integer, default=0)
    status = Column(String(20), default=DocumentStatus.UPLOADED.value, index=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<Document id={self.id} status={self.status} filename={self.filename}>"


class QARecord(Base):
    """问答记录表。

    关联 Document.id（逻辑外键，不设物理约束以兼容 SQLite 简单迁移）。
    """

    __tablename__ = "qa_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(36), nullable=False, index=True)  # 关联 Document.id
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<QARecord id={self.id} document_id={self.document_id}>"
