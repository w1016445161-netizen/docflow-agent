import os
import logging
import time
from pathlib import Path

import fitz
import pytesseract
from PIL import Image
from dotenv import load_dotenv

from backend.core.logging import log_event

_logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


def setup_tesseract():
    """
    配置 Tesseract OCR 程序路径。
    Windows 下通常需要手动指定 tesseract.exe。
    """
    tesseract_cmd = os.getenv("TESSERACT_CMD", "").strip()

    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd


def render_pdf_page_to_image(page, dpi: int = 200) -> Image.Image:
    """
    把 PDF 单页渲染成 PIL 图片。
    """
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    pix = page.get_pixmap(matrix=matrix, alpha=False)

    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    return image


def ocr_image(image: Image.Image, lang: str = "chi_sim+eng") -> str:
    """
    对单张图片做 OCR。
    """
    setup_tesseract()

    text = pytesseract.image_to_string(image, lang=lang)

    return text.strip()


def ocr_pdf(file_path: str) -> str:
    """
    对扫描型 PDF 做 OCR。

    每条 OCR 日志记录识别参数（DPI、语言、页数限制），
    以及逐页识别进度和总耗时。
    """
    t0 = time.time()
    setup_tesseract()

    path = Path(file_path)

    if not path.exists():
        error_msg = f"文件不存在：{file_path}"
        log_event(_logger, logging.ERROR, error_msg, operation="ocr", error_detail=error_msg)
        raise FileNotFoundError(error_msg)

    lang = os.getenv("OCR_LANG", "chi_sim+eng")
    dpi = int(os.getenv("OCR_DPI", "200"))
    max_pages = int(os.getenv("OCR_MAX_PAGES", "20"))

    log_event(_logger, logging.INFO, "OCR 开始处理",
              operation="ocr",
              extra_fields={"dpi": dpi, "lang": lang, "max_pages": max_pages})

    doc = fitz.open(file_path)

    pages_text = []

    total_pages = len(doc)
    pages_to_process = min(total_pages, max_pages)

    for page_index in range(pages_to_process):
        page_start = time.time()
        page = doc[page_index]

        image = render_pdf_page_to_image(page, dpi=dpi)
        text = ocr_image(image, lang=lang)

        page_duration = (time.time() - page_start) * 1000
        log_event(_logger, logging.INFO, f"OCR 第 {page_index + 1}/{pages_to_process} 页完成",
                  operation="ocr", duration_ms=page_duration,
                  extra_fields={"page": page_index + 1, "page_text_length": len(text)})

        pages_text.append(f"\n[第 {page_index + 1} 页 OCR 识别结果]\n{text}")

    doc.close()

    if total_pages > max_pages:
        pages_text.append(
            f"\n[提示] 当前 PDF 共 {total_pages} 页，OCR_MAX_PAGES={max_pages}，仅识别前 {max_pages} 页。"
        )

    total_duration = (time.time() - t0) * 1000
    log_event(_logger, logging.INFO, f"OCR 全部完成，共处理 {pages_to_process} 页",
              operation="ocr", duration_ms=total_duration,
              extra_fields={"total_pages": total_pages, "pages_processed": pages_to_process})

    return "\n".join(pages_text).strip()


def check_ocr_available() -> dict:
    """
    检查 OCR 环境是否可用。
    """
    setup_tesseract()

    try:
        version = str(pytesseract.get_tesseract_version())
        languages = pytesseract.get_languages(config="")

        return {
            "available": True,
            "version": version,
            "languages": languages,
            "tesseract_cmd": pytesseract.pytesseract.tesseract_cmd,
        }

    except Exception as e:
        return {
            "available": False,
            "error": str(e),
            "tesseract_cmd": pytesseract.pytesseract.tesseract_cmd,
        }
