from table_analyzer import analyze_excel, excel_analysis_to_text
from pathlib import Path
from pypdf import PdfReader
from docx import Document


def parse_txt(file_path: str) -> str:
    path = Path(file_path)
    return path.read_text(encoding="utf-8", errors="ignore")


def parse_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    pages_text = []

    for page_index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages_text.append(f"\n[第 {page_index} 页]\n{text}")

    return "\n".join(pages_text)


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