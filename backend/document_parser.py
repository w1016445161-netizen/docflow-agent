import os
import logging
import time
from pathlib import Path

from pypdf import PdfReader
from docx import Document
from dotenv import load_dotenv

from backend.ocr_parser import ocr_pdf
from backend.table_analyzer import analyze_excel, excel_analysis_to_text

from backend.core.logging import log_event

_logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


def _get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name, str(default)).lower()
    return value in {"1", "true", "yes", "on"}


def parse_txt(file_path: str) -> str:
    path = Path(file_path)
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def parse_pdf(file_path: str) -> str:
    """解析 PDF 文件，自动判断使用文本提取还是 OCR。

    日志记录解析方式（text/ocr）及耗时，方便后续分析解析效果。
    """
    t0 = time.time()
    texts = []

    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                texts.append(page_text.strip())
    except Exception as exc:
        log_event(_logger, logging.WARNING, f"PDF 文本提取异常: {exc}",
                  operation="parse", error_detail=str(exc))
        texts = []

    text = "\n\n".join(texts).strip()

    min_text_length = int(os.getenv("OCR_MIN_TEXT_LENGTH", "80"))

    if len(text) >= min_text_length:
        duration = (time.time() - t0) * 1000
        log_event(_logger, logging.INFO, "PDF 文本提取完成",
                  operation="parse", duration_ms=duration,
                  extra_fields={"parse_method": "text", "text_length": len(text)})
        return text

    # 文本提取不足，判断是否满足 OCR 触发条件
    log_event(_logger, logging.INFO,
              f"PDF 文本提取不足（{len(text)} < {min_text_length}），准备触发 OCR",
              operation="parse",
              extra_fields={"parse_method": "text", "text_length": len(text),
                            "min_text_length": min_text_length})

    if _get_bool("OCR_ENABLED", False):
        ocr_text = ocr_pdf(file_path)
        duration = (time.time() - t0) * 1000
        log_event(_logger, logging.INFO, "PDF OCR 解析完成",
                  operation="parse", duration_ms=duration,
                  extra_fields={"parse_method": "ocr", "text_length": len(ocr_text)})
        return ocr_text

    duration = (time.time() - t0) * 1000
    log_event(_logger, logging.WARNING, "PDF 解析完成但未提取到有效文本",
              operation="parse", duration_ms=duration, error_detail="text_length=0")

    if text:
        return text

    raise ValueError("没有从 PDF 中提取到有效文本。如果这是扫描型 PDF，请启用 OCR。")


def parse_docx(file_path: str) -> str:
    doc = Document(file_path)
    paragraphs = []

    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs)


def parse_document(file_path: str) -> str:
    suffix = Path(file_path).suffix.lower()

    if suffix in [".txt", ".md"]:
        return parse_txt(file_path)

    if suffix == ".pdf":
        return parse_pdf(file_path)

    if suffix == ".docx":
        return parse_docx(file_path)

    if suffix in [".xlsx", ".xls"]:
        analysis = analyze_excel(file_path)
        return excel_analysis_to_text(analysis)

    raise ValueError(f"暂不支持该文件类型：{suffix}")
