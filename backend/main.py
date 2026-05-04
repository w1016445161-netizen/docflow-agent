import json
import uuid
import shutil
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.document_parser import parse_document
from backend.chunker import chunk_text
from backend.retriever import retrieve_chunks
from backend.llm_client import ask_llm, summarize_text
from backend.report import save_markdown_report
from backend.table_analyzer import analyze_excel
from backend.chart_generator import generate_excel_charts
from backend.memory import load_memory, update_memory, add_history, memory_to_text
from backend.multi_doc import list_documents, build_multi_doc_context
from backend.ocr_parser import check_ocr_available


app = FastAPI(
    title="DocFlow-Agent API",
    description="文档智能体后端服务",
    version="0.3.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


UPLOAD_DIR = Path("storage/uploads")
INDEX_DIR = Path("storage/index")
OUTPUT_DIR = Path("storage/outputs")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")


class AskRequest(BaseModel):
    doc_id: str
    question: str


class MemoryUpdateRequest(BaseModel):
    key: str
    value: str


class CompareRequest(BaseModel):
    doc_ids: list[str]
    question: str = "请比较这些文档的主要内容、共同点和差异点。"


@app.get("/")
def root():
    return {
        "message": "DocFlow-Agent backend is running."
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "DocFlow-Agent backend is running."
    }


@app.get("/api/health")
def api_health_check():
    return {
        "status": "ok",
        "message": "DocFlow-Agent backend is running."
    }


@app.get("/ocr/status")
def ocr_status():
    return check_ocr_available()


@app.post("/api/documents/summarize")
async def summarize_document(file: UploadFile = File(...)):
    original_filename = file.filename or "unknown"
    suffix = Path(original_filename).suffix.lower()

    if suffix not in [".txt", ".pdf"]:
        raise HTTPException(
            status_code=400,
            detail="暂时只支持 .txt 和 .pdf 文件。"
        )

    doc_id = str(uuid.uuid4())
    saved_path = UPLOAD_DIR / f"{doc_id}{suffix}"

    with saved_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        text = parse_document(str(saved_path))
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"文档解析失败：{e}"
        )

    char_count = len(text)
    max_chars = 12000
    limited_text = text[:max_chars]
    is_truncated = char_count > max_chars

    summary = summarize_text(original_filename, limited_text)

    preview = text[:500]
    file_type = suffix.lstrip(".")

    return {
        "filename": original_filename,
        "file_type": file_type,
        "char_count": char_count,
        "is_truncated": is_truncated,
        "preview": preview,
        "summary": summary,
        "model": "docflow-agent",
        "usage": None,
    }


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    doc_id = str(uuid.uuid4())

    original_filename = file.filename or "unknown_file"
    suffix = Path(original_filename).suffix.lower()

    if suffix not in [".pdf", ".docx", ".txt", ".md", ".xlsx", ".xls"]:
        return {
            "error": f"暂不支持该文件类型：{suffix}",
            "supported_types": [".pdf", ".docx", ".txt", ".md", ".xlsx", ".xls"]
        }

    saved_path = UPLOAD_DIR / f"{doc_id}{suffix}"

    with saved_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        text = parse_document(str(saved_path))
    except Exception as e:
        return {
            "error": "文档解析失败",
            "detail": str(e)
        }

    chunks = chunk_text(text)

    chart_paths = []
    excel_analysis = None

    if suffix in [".xlsx", ".xls"]:
        try:
            excel_analysis = analyze_excel(str(saved_path))
            chart_paths = generate_excel_charts(str(saved_path), doc_id)
        except Exception as e:
            excel_analysis = {
                "error": "Excel 分析或图表生成失败",
                "detail": str(e)
            }

    index_data = {
        "doc_id": doc_id,
        "filename": original_filename,
        "file_path": str(saved_path),
        "file_type": suffix,
        "total_chars": len(text),
        "total_chunks": len(chunks),
        "chunks": chunks,
        "excel_analysis": excel_analysis,
        "chart_paths": chart_paths
    }

    index_path = INDEX_DIR / f"{doc_id}.json"
    index_path.write_text(
        json.dumps(index_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    add_history("upload", f"上传文档：{original_filename}")

    return {
        "message": "文档上传并解析成功",
        "doc_id": doc_id,
        "filename": original_filename,
        "file_type": suffix,
        "total_chars": len(text),
        "total_chunks": len(chunks),
        "chart_paths": chart_paths
    }


@app.post("/ask")
def ask_document(request: AskRequest):
    index_path = INDEX_DIR / f"{request.doc_id}.json"

    if not index_path.exists():
        return {
            "error": "找不到该 doc_id 对应的文档索引"
        }

    index_data = json.loads(index_path.read_text(encoding="utf-8"))
    chunks = index_data["chunks"]

    related_chunks = retrieve_chunks(request.question, chunks, top_k=4)

    memory_context = {
        "chunk_id": "memory",
        "text": memory_to_text(),
        "score": 0
    }

    contexts = [memory_context] + related_chunks

    answer = ask_llm(request.question, contexts)

    report_path = save_markdown_report(
        doc_id=request.doc_id,
        question=request.question,
        answer=answer
    )

    add_history("ask", f"针对文档 {index_data['filename']} 提问：{request.question}")

    return {
        "doc_id": request.doc_id,
        "filename": index_data["filename"],
        "question": request.question,
        "answer": answer,
        "related_chunks": related_chunks,
        "report_path": report_path
    }


@app.get("/documents")
def get_documents():
    return {
        "documents": list_documents()
    }


@app.get("/documents/{doc_id}")
def get_document_info(doc_id: str):
    index_path = INDEX_DIR / f"{doc_id}.json"

    if not index_path.exists():
        return {
            "error": "找不到该 doc_id 对应的文档索引"
        }

    index_data = json.loads(index_path.read_text(encoding="utf-8"))

    return {
        "doc_id": index_data["doc_id"],
        "filename": index_data["filename"],
        "file_path": index_data["file_path"],
        "file_type": index_data.get("file_type"),
        "total_chars": index_data["total_chars"],
        "total_chunks": index_data["total_chunks"],
        "excel_analysis": index_data.get("excel_analysis"),
        "chart_paths": index_data.get("chart_paths", [])
    }


@app.post("/excel/analyze")
async def analyze_excel_api(file: UploadFile = File(...)):
    doc_id = str(uuid.uuid4())

    original_filename = file.filename or "unknown_excel"
    suffix = Path(original_filename).suffix.lower()

    if suffix not in [".xlsx", ".xls"]:
        return {
            "error": "请上传 .xlsx 或 .xls 文件"
        }

    saved_path = UPLOAD_DIR / f"{doc_id}{suffix}"

    with saved_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    analysis = analyze_excel(str(saved_path))
    chart_paths = generate_excel_charts(str(saved_path), doc_id)

    add_history("excel_analyze", f"分析 Excel 文件：{original_filename}")

    return {
        "doc_id": doc_id,
        "filename": original_filename,
        "analysis": analysis,
        "chart_paths": chart_paths
    }


@app.get("/memory")
def get_memory():
    return load_memory()


@app.post("/memory")
def update_user_memory(request: MemoryUpdateRequest):
    memory = update_memory(request.key, request.value)

    return {
        "message": "记忆更新成功",
        "memory": memory
    }


@app.post("/compare")
def compare_documents(request: CompareRequest):
    if len(request.doc_ids) < 2:
        return {
            "error": "至少需要传入两个 doc_id 才能进行多文档对比"
        }

    try:
        contexts = build_multi_doc_context(request.doc_ids, max_chunks_per_doc=3)
    except Exception as e:
        return {
            "error": "构建多文档上下文失败",
            "detail": str(e)
        }

    answer = ask_llm(request.question, contexts)

    add_history("compare", f"对比文档：{', '.join(request.doc_ids)}")

    return {
        "doc_ids": request.doc_ids,
        "question": request.question,
        "answer": answer,
        "contexts": contexts
    }