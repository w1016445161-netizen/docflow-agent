from io import BytesIO
from pathlib import Path
from typing import Tuple

from fastapi import UploadFile, HTTPException
from pypdf import PdfReader

MAX_TEXT_CHARS = 12000


async def extract_text_from_upload(file: UploadFile) -> Tuple[str, str, int]:
    """
    从上传的 TXT / PDF 文件中提取文本。

    返回：
    text: 提取出的文本
    file_type: 文件类型
    char_count: 原始文本字符数
    """
    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()

    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="上传文件为空。")

    if suffix == ".txt":
        text = extract_text_from_txt(content)
        file_type = "txt"
    elif suffix == ".pdf":
        text = extract_text_from_pdf(content)
        file_type = "pdf"
    else:
        raise HTTPException(
            status_code=400,
            detail="暂时只支持 .txt 和 .pdf 文件。",
        )

    text = clean_text(text)

    if not text:
        raise HTTPException(
            status_code=400,
            detail="没有从文档中提取到有效文本。如果是扫描版 PDF，需要后续接入 OCR。",
        )

    return text, file_type, len(text)


def extract_text_from_txt(content: bytes) -> str:
    """
    尝试用多种编码读取 TXT。
    """
    encodings = ["utf-8", "utf-8-sig", "gbk", "gb18030"]

    for encoding in encodings:
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue

    return content.decode("utf-8", errors="ignore")


def extract_text_from_pdf(content: bytes) -> str:
    """
    从 PDF 中提取文本。
    """
    try:
        reader = PdfReader(BytesIO(content))
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"PDF 解析失败：{exc}",
        )

    page_texts = []

    for index, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""

        if page_text.strip():
            page_texts.append(f"\n\n【第 {index} 页】\n{page_text}")

    return "\n".join(page_texts)


def clean_text(text: str) -> str:
    """
    清理文本中过多的空白。
    """
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def limit_text_for_llm(text: str) -> Tuple[str, bool]:
    """
    限制输入给大模型的文本长度，避免一次请求过长。
    """
    if len(text) <= MAX_TEXT_CHARS:
        return text, False

    return text[:MAX_TEXT_CHARS], True


def build_summary_prompt(filename: str, text: str, is_truncated: bool) -> str:
    """
    构造文档摘要 Prompt。
    """
    truncate_notice = ""

    if is_truncated:
        truncate_notice = (
            "\n注意：由于文档较长，以下内容只截取了前半部分。"
            "请基于已提供内容生成摘要，并在最后说明摘要基于截取内容生成。\n"
        )

    return f"""
你是一个专业的文档处理智能体。请阅读下面的文档内容，并生成结构化摘要。

文档名称：{filename}
{truncate_notice}

请按照以下格式输出：

## 一、文档主要内容

用 3 到 5 句话概括文档核心内容。

## 二、关键信息提取

提取文档中的重要人物、时间、地点、概念、数据、结论或任务。

## 三、结构化要点

用有序列表总结文档中的主要段落或逻辑结构。

## 四、可能的后续问题

提出 3 个用户可能继续追问的问题。

以下是文档内容：

{text}
""".strip()
