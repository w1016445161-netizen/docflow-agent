import os
from pathlib import Path

from pypdf import PdfReader
from docx import Document

from backend.table_analyzer import analyze_excel, excel_analysis_to_text
from backend.ocr_parser import ocr_pdf


def parse_txt(file_path: str) -> str:
    path = Path(file_path)
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def parse_pdf_text_only(file_path: str) -> str:
    """
    只使用 pypdf 提取 PDF 文本。
    适合数字文本型 PDF。
    """
    reader = PdfReader(file_path)
    pages_text = []

    for page_index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages_text.append(f"\n[第 {page_index} 页]\n{text}")

    return "\n".join(pages_text).strip()


def parse_pdf(file_path: str) -> str:
    """
    PDF 解析逻辑：
    1. 先尝试普通文本提取
    2. 如果提取结果太少，判断为扫描型 PDF
    3. 自动启用 OCR
    """
    normal_text = parse_pdf_text_only(file_path)

    ocr_enabled = os.getenv("OCR_ENABLED", "false").lower() == "true"
    min_text_length = int(os.getenv("OCR_MIN_TEXT_LENGTH", "80"))

    if len(normal_text.strip()) >= min_text_length:
        return normal_text

    if not ocr_enabled:
        return (
            normal_text
            + "\n\n[提示] 该 PDF 可能是扫描型 PDF，普通文本提取结果较少。"
            + "请在 .env 中设置 OCR_ENABLED=true 后启用 OCR。"
        )

    try:
        ocr_text = ocr_pdf(file_path)

        if not ocr_text.strip():
            return (
                normal_text
                + "\n\n[提示] 已尝试 OCR，但未识别到有效文本。"
            )

        return (
            "[系统提示] 普通 PDF 文本提取结果较少，已自动启用 OCR 识别。\n\n"
            + ocr_text
        )

    except Exception as e:
        return (
            normal_text
            + "\n\n[错误] OCR 识别失败："
            + str(e)
        )


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