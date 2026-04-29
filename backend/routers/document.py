from typing import Optional, Dict, Any

from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel

from backend.services.document_service import (
    extract_text_from_upload,
    limit_text_for_llm,
    build_summary_prompt,
)
from backend.services.llm_service import llm_service


router = APIRouter(prefix="/api/documents", tags=["documents"])


class DocumentSummaryResponse(BaseModel):
    filename: str
    file_type: str
    char_count: int
    is_truncated: bool
    preview: str
    summary: str
    model: str
    usage: Optional[Dict[str, Any]] = None


@router.post("/summarize", response_model=DocumentSummaryResponse)
async def summarize_document(file: UploadFile = File(...)):
    text, file_type, char_count = await extract_text_from_upload(file)

    limited_text, is_truncated = limit_text_for_llm(text)

    prompt = build_summary_prompt(
        filename=file.filename or "unknown",
        text=limited_text,
        is_truncated=is_truncated,
    )

    result = llm_service.chat(
        user_prompt=prompt,
        system_prompt="你是一个严谨、清晰、擅长文档总结和信息提取的中文文档智能体。",
        temperature=0.2,
    )

    preview = text[:500]

    return {
        "filename": file.filename or "unknown",
        "file_type": file_type,
        "char_count": char_count,
        "is_truncated": is_truncated,
        "preview": preview,
        "summary": result["content"],
        "model": result["model"],
        "usage": result["usage"],
    }