import json
import uuid
import shutil
import time
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.document_parser import parse_document
from backend.chunker import chunk_text
from backend.retriever import retrieve_chunks_rag
from backend.llm_client import ask_llm, summarize_text, summarize_text_stream
from backend.report import save_markdown_report
from backend.table_analyzer import analyze_excel
from backend.chart_generator import generate_excel_charts
from backend.memory import load_memory, update_memory, add_history, memory_to_text
from backend.multi_doc import build_multi_doc_context
from backend.ocr_parser import check_ocr_available

from backend.core.response import ApiResponse
from backend.core.exceptions import AppException, DocumentNotFoundError
from backend.core.logging import (
    setup_logging,
    set_request_id,
    reset_request_id,
    log_event,
)
from backend.database import init_db, SessionLocal
from backend.models import Document, DocumentStatus, QARecord
from backend.schemas import DocumentStatusOut
from backend.embedding_service import embed_texts
from backend.vector_store import save_vectors

_logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化日志+数据库，关闭时清理。"""
    setup_logging()
    init_db()
    yield


app = FastAPI(
    title="DocFlow-Agent API",
    description="文档智能体后端服务",
    version="0.3.0",
    lifespan=lifespan,
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


_SUMMARY_MODES = {
    "fast": {"max_chars": 6000, "max_tokens": 800, "label": "快速摘要"},
    "deep": {"max_chars": 20000, "max_tokens": 1800, "label": "深度摘要"},
}

UPLOAD_DIR = Path("storage/uploads")
INDEX_DIR = Path("storage/index")
OUTPUT_DIR = Path("storage/outputs")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")


def _get_index_value(doc_id: str, key: str, default=None):
    """从文件存储的索引 JSON 中读取指定字段（过渡期兼容）。"""
    index_path = INDEX_DIR / f"{doc_id}.json"
    if index_path.exists():
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
            return data.get(key, default)
        except (json.JSONDecodeError, OSError):
            return default
    return default


# ── 请求入口中间件 ──


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    """为每个请求注入 request_id，注入到 contextvars 供日志系统使用。

    设计决策：使用 contextvars 而非 request.state 传递 request_id，
    因为日志调用分散在各模块的函数中，contextvars 无需层层传参即可读取。
    """
    request_id = str(uuid.uuid4())
    token = set_request_id(request_id)
    request.state.request_id = request_id

    try:
        response = await call_next(request)
        # 在响应头中透传 request_id，方便前端或调试工具追踪
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception:
        # 理论上所有异常已被 exception_handler 捕获并转为正常响应，
        # 此处仅做兜底，避免中间件拦截未处理的异常
        raise
    finally:
        reset_request_id(token)


# ── 全局异常处理器 ──

# 设计决策：只为 Exception 注册一个处理器，内部通过 isinstance 分发。
# 虽然需要额外为 HTTPException 注册以确保覆盖 Starlette 的默认处理器，
# 但实际处理逻辑仍在同一函数中，新增异常类型时无需修改此处。
@app.exception_handler(HTTPException)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """全局统一异常处理器。

    处理链：
    1. AppException（业务异常）       → 使用异常的 code/message/http_status_code
    2. HTTPException（FastAPI 内置）  → 状态码 * 100 转为业务码
    3. Exception（未预期异常）        → 50000，记录堆栈
    """
    req_id = getattr(request.state, "request_id", "") or ""

    if isinstance(exc, AppException):
        code = exc.code
        message = exc.message
        status_code = exc.http_status_code
        log_event(_logger, logging.WARNING, message, operation="exception",
                  error_detail=message, file_id="")
    elif isinstance(exc, HTTPException):
        code = exc.status_code * 100
        message = exc.detail
        status_code = exc.status_code
        log_event(_logger, logging.WARNING, f"HTTP {exc.status_code}: {exc.detail}",
                  operation="exception", error_detail=str(exc.detail))
    else:
        code = 50000
        message = "服务器内部错误"
        status_code = 500
        log_event(_logger, logging.ERROR, f"未捕获异常: {exc}",
                  operation="exception", error_detail=str(exc), exc_info=True)

    resp = ApiResponse(code=code, message=message, data=None, request_id=req_id)
    return JSONResponse(status_code=status_code, content=resp.model_dump())




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
    return {"message": "DocFlow-Agent backend is running."}


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "DocFlow-Agent backend is running."}


@app.get("/api/health")
def api_health_check():
    return {"status": "ok", "message": "DocFlow-Agent backend is running."}


@app.get("/ocr/status")
def ocr_status():
    return check_ocr_available()


@app.post("/api/documents/summarize")
async def summarize_document(
    file: UploadFile = File(...), summary_mode: str = Form("fast")
):
    original_filename = file.filename or "unknown"
    suffix = Path(original_filename).suffix.lower()
    t0 = time.time()

    log_event(_logger, logging.INFO, f"摘要请求开始：{original_filename}",
              operation="summarize")

    if suffix not in [".txt", ".pdf"]:
        raise HTTPException(status_code=400, detail="暂时只支持 .txt 和 .pdf 文件。")

    doc_id = str(uuid.uuid4())
    saved_path = UPLOAD_DIR / f"{doc_id}{suffix}"

    with saved_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Session 1：上传 → 解析 → 分块 → 写入索引 → PARSED
    file_type = suffix.lstrip(".")
    db = SessionLocal()
    try:
        db_doc = Document(
            id=doc_id, filename=original_filename, file_type=file_type,
            storage_path=str(saved_path), parse_method="unknown",
            status=DocumentStatus.UPLOADED.value,
        )
        db.add(db_doc)
        db.commit()

        db_doc.status = DocumentStatus.PARSING.value
        db.commit()

        try:
            text, parse_method = parse_document(str(saved_path))
        except Exception as e:
            db_doc.status = DocumentStatus.FAILED.value
            db_doc.error_message = str(e)
            db.commit()
            raise HTTPException(status_code=400, detail=f"文档解析失败：{e}")

        t2 = time.time()
        log_event(_logger, logging.INFO, "文档解析完成", operation="parse",
                  duration_ms=(t2 - t0) * 1000, file_id=doc_id)

        db_doc.parse_method = parse_method
        db_doc.char_count = len(text)

        mode_cfg = _SUMMARY_MODES.get(summary_mode, _SUMMARY_MODES["fast"])
        char_count = len(text)
        max_chars = mode_cfg["max_chars"]
        limited_text = text[:max_chars]
        is_truncated = char_count > max_chars

        chunks = chunk_text(text)

        index_data = {
            "doc_id": doc_id, "filename": original_filename, "file_path": str(saved_path),
            "file_type": suffix, "total_chars": char_count, "total_chunks": len(chunks),
            "chunks": chunks,
        }

        index_path = INDEX_DIR / f"{doc_id}.json"
        index_path.write_text(
            json.dumps(index_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # 索引写入成功后才标记 PARSED
        db_doc.status = DocumentStatus.PARSED.value
        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        db_doc.status = DocumentStatus.FAILED.value
        db_doc.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=400, detail=f"文档解析失败：{e}")
    finally:
        db.close()

    # Session 2：LLM 摘要 → READY / FAILED
    db = SessionLocal()
    try:
        d = db.query(Document).filter(Document.id == doc_id).first()
        d.status = DocumentStatus.SUMMARIZING.value
        db.commit()

        try:
            summary = summarize_text(
                original_filename, limited_text, max_tokens=mode_cfg["max_tokens"]
            )
        except Exception:
            d.status = DocumentStatus.FAILED.value
            d.error_message = "LLM 摘要失败"
            db.commit()
            raise

        d.status = DocumentStatus.READY.value
        db.commit()
    finally:
        db.close()

    t4 = time.time()
    log_event(_logger, logging.INFO, "LLM 摘要完成", operation="llm",
              duration_ms=(t4 - t2) * 1000, file_id=doc_id)

    preview = text[:500]
    file_type = suffix.lstrip(".")

    duration = (time.time() - t0) * 1000
    log_event(_logger, logging.INFO, f"摘要请求完成：{original_filename}",
              operation="summarize", duration_ms=duration, file_id=doc_id)

    return {
        "doc_id": doc_id,
        "summary_mode": summary_mode,
        "filename": original_filename,
        "file_type": file_type,
        "char_count": char_count,
        "is_truncated": is_truncated,
        "preview": preview,
        "summary": summary,
        "model": "docflow-agent",
        "usage": None,
    }


@app.post("/api/documents/summarize/stream")
async def summarize_document_stream(
    file: UploadFile = File(...), summary_mode: str = Form("fast")
):
    original_filename = file.filename or "unknown"
    suffix = Path(original_filename).suffix.lower()

    if suffix not in [".txt", ".pdf"]:
        raise HTTPException(status_code=400, detail="暂时只支持 .txt 和 .pdf 文件。")

    doc_id = str(uuid.uuid4())
    saved_path = UPLOAD_DIR / f"{doc_id}{suffix}"

    with saved_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    parse_method = "unknown"
    try:
        text, parse_method = parse_document(str(saved_path))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文档解析失败：{e}")

    # 创建文档记录，初始状态为 parsed（解析已在生成器外完成）
    file_type = suffix.lstrip(".")
    db = SessionLocal()
    try:
        db_doc = Document(
            id=doc_id, filename=original_filename, file_type=file_type,
            storage_path=str(saved_path), parse_method=parse_method,
            char_count=len(text), status=DocumentStatus.PARSED.value,
        )
        db.add(db_doc)
        db.commit()
    finally:
        db.close()

    mode_cfg = _SUMMARY_MODES.get(summary_mode, _SUMMARY_MODES["fast"])
    char_count = len(text)
    max_chars = mode_cfg["max_chars"]
    limited_text = text[:max_chars]
    is_truncated = char_count > max_chars

    chunks = chunk_text(text)

    index_data = {
        "doc_id": doc_id,
        "filename": original_filename,
        "file_path": str(saved_path),
        "file_type": suffix,
        "total_chars": char_count,
        "total_chunks": len(chunks),
        "chunks": chunks,
    }

    index_path = INDEX_DIR / f"{doc_id}.json"
    index_path.write_text(
        json.dumps(index_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    preview = text[:500]

    def generate():
        db_gen = SessionLocal()
        try:
            # 更新状态为 summarizing
            d = db_gen.query(Document).filter(Document.id == doc_id).first()
            if d:
                d.status = DocumentStatus.SUMMARIZING.value
                db_gen.commit()

            yield json.dumps(
                {"type": "status", "data": "文档解析完成，正在生成摘要..."},
                ensure_ascii=False,
            ) + "\n"

            yield json.dumps(
                {
                    "type": "meta",
                    "data": {
                        "summary_mode": summary_mode,
                        "doc_id": doc_id,
                        "filename": original_filename,
                        "file_type": file_type,
                        "char_count": char_count,
                        "is_truncated": is_truncated,
                        "preview": preview,
                    },
                },
                ensure_ascii=False,
            ) + "\n"

            for delta in summarize_text_stream(
                original_filename, limited_text, max_tokens=mode_cfg["max_tokens"]
            ):
                yield json.dumps(
                    {"type": "delta", "data": delta}, ensure_ascii=False
                ) + "\n"

            # 摘要完成，更新状态为 ready
            d = db_gen.query(Document).filter(Document.id == doc_id).first()
            if d:
                d.status = DocumentStatus.READY.value
                db_gen.commit()

            yield json.dumps({"type": "done", "data": ""}, ensure_ascii=False) + "\n"
        except Exception as e:
            # 失败时更新状态为 failed
            d = db_gen.query(Document).filter(Document.id == doc_id).first()
            if d:
                d.status = DocumentStatus.FAILED.value
                d.error_message = str(e)
                db_gen.commit()
            yield json.dumps(
                {"type": "error", "data": str(e)}, ensure_ascii=False
            ) + "\n"
        finally:
            db_gen.close()

    return StreamingResponse(generate(), media_type="application/x-ndjson")


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    doc_id = str(uuid.uuid4())
    original_filename = file.filename or "unknown_file"
    t0 = time.time()

    log_event(_logger, logging.INFO, f"文档上传开始：{original_filename}",
              operation="upload", file_id=doc_id)

    suffix = Path(original_filename).suffix.lower()

    if suffix not in [".pdf", ".docx", ".txt", ".md", ".xlsx", ".xls"]:
        log_event(_logger, logging.WARNING, f"不支持的文件类型：{suffix}",
                  operation="upload", file_id=doc_id)
        return {
            "error": f"暂不支持该文件类型：{suffix}",
            "supported_types": [".pdf", ".docx", ".txt", ".md", ".xlsx", ".xls"],
        }

    saved_path = UPLOAD_DIR / f"{doc_id}{suffix}"

    with saved_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 创建文档元数据记录，晚于索引写入后设为 PARSED，避免中间步骤失败时状态残留
    file_type = suffix.lstrip(".")
    db = SessionLocal()
    try:
        db_doc = Document(
            id=doc_id,
            filename=original_filename,
            file_type=file_type,
            storage_path=str(saved_path),
            parse_method="unknown",
            status=DocumentStatus.UPLOADED.value,
        )
        db.add(db_doc)
        db.commit()

        db_doc.status = DocumentStatus.PARSING.value
        db.commit()

        try:
            text, parse_method = parse_document(str(saved_path))
        except Exception as e:
            db_doc.status = DocumentStatus.FAILED.value
            db_doc.error_message = str(e)
            db.commit()
            log_event(_logger, logging.ERROR, f"文档解析失败：{original_filename}",
                      operation="parse", file_id=doc_id, error_detail=str(e))
            return {"error": "文档解析失败", "detail": str(e)}

        db_doc.parse_method = parse_method
        db_doc.char_count = len(text)

        chunks = chunk_text(text)

        index_data = {
            "doc_id": doc_id,
            "filename": original_filename,
            "file_path": str(saved_path),
            "file_type": suffix,
            "total_chars": len(text),
            "total_chunks": len(chunks),
            "chunks": chunks,
        }

        index_path = INDEX_DIR / f"{doc_id}.json"
        index_path.write_text(
            json.dumps(index_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # 索引文件写入成功后才标记解析完成
        db_doc.status = DocumentStatus.PARSED.value
        db.commit()
    except Exception as e:
        db_doc.status = DocumentStatus.FAILED.value
        db_doc.error_message = str(e)
        db.commit()
        log_event(_logger, logging.ERROR, f"文档处理失败：{original_filename}",
                  operation="upload", file_id=doc_id, error_detail=str(e))
        return {"error": "文档处理失败", "detail": str(e)}
    finally:
        db.close()

    chart_paths = []
    excel_analysis = None

    chart_paths = []
    excel_analysis = None

    if suffix in [".xlsx", ".xls"]:
        try:
            excel_analysis = analyze_excel(str(saved_path))
            chart_paths = generate_excel_charts(str(saved_path), doc_id)
        except Exception as e:
            excel_analysis = {"error": "Excel 分析或图表生成失败", "detail": str(e)}

    index_data = {
        "doc_id": doc_id,
        "filename": original_filename,
        "file_path": str(saved_path),
        "file_type": suffix,
        "total_chars": len(text),
        "total_chunks": len(chunks),
        "chunks": chunks,
        "excel_analysis": excel_analysis,
        "chart_paths": chart_paths,
    }

    index_path = INDEX_DIR / f"{doc_id}.json"
    index_path.write_text(
        json.dumps(index_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # RAG: 生成向量 embeddings 并保存，失败不阻断上传
    try:
        t_emb = time.time()
        chunk_texts = [c["text"] for c in chunks]
        embeddings = embed_texts(chunk_texts)
        save_vectors(doc_id, chunks, embeddings)
        emb_duration = (time.time() - t_emb) * 1000
        log_event(
            _logger,
            logging.INFO,
            "向量索引已保存",
            operation="embedding",
            duration_ms=emb_duration,
            file_id=doc_id,
            extra_fields={"chunk_count": len(chunks), "embedding_dim": 256},
        )
    except Exception as e:
        log_event(
            _logger,
            logging.WARNING,
            f"向量索引生成失败，后续将使用关键词检索: {e}",
            operation="embedding",
            file_id=doc_id,
            error_detail=str(e),
        )

    add_history("upload", f"上传文档：{original_filename}")

    duration = (time.time() - t0) * 1000
    log_event(_logger, logging.INFO, f"文档上传完成：{original_filename}",
              operation="upload", duration_ms=duration, file_id=doc_id)

    return {
        "message": "文档上传并解析成功",
        "doc_id": doc_id,
        "filename": original_filename,
        "file_type": suffix,
        "total_chars": len(text),
        "total_chunks": len(chunks),
        "chart_paths": chart_paths,
    }


@app.post("/ask")
def ask_document(request: AskRequest):
    t0 = time.time()
    log_event(_logger, logging.INFO, f"问答请求：doc_id={request.doc_id}",
              operation="query", file_id=request.doc_id)

    index_path = INDEX_DIR / f"{request.doc_id}.json"

    if not index_path.exists():
        log_event(_logger, logging.WARNING, f"文档不存在：{request.doc_id}",
                  operation="query", file_id=request.doc_id)
        return {"error": "找不到该 doc_id 对应的文档索引"}

    index_data = json.loads(index_path.read_text(encoding="utf-8"))
    chunks = index_data["chunks"]

    related_chunks = retrieve_chunks_rag(request.doc_id, request.question, chunks, top_k=4)

    memory_context = {"chunk_id": "memory", "text": memory_to_text(), "score": 0}

    contexts = [memory_context] + related_chunks

    answer = ask_llm(request.question, contexts)

    report_path = save_markdown_report(
        doc_id=request.doc_id, question=request.question, answer=answer
    )

    add_history("ask", f"针对文档 {index_data['filename']} 提问：{request.question}")

    # 保存问答记录到数据库
    db = SessionLocal()
    try:
        qa = QARecord(
            document_id=request.doc_id,
            question=request.question,
            answer=answer,
        )
        db.add(qa)
        db.commit()
        log_event(_logger, logging.INFO, "问答记录已保存",
                  operation="query", file_id=request.doc_id)
    except Exception as e:
        log_event(_logger, logging.WARNING, f"问答记录保存失败: {e}",
                  operation="query", file_id=request.doc_id, error_detail=str(e))
    finally:
        db.close()

    duration = (time.time() - t0) * 1000
    log_event(_logger, logging.INFO, f"问答完成：doc_id={request.doc_id}",
              operation="query", duration_ms=duration, file_id=request.doc_id)

    return {
        "doc_id": request.doc_id,
        "filename": index_data["filename"],
        "question": request.question,
        "answer": answer,
        "related_chunks": related_chunks,
        "report_path": report_path,
    }


@app.get("/documents")
def get_documents():
    # 从数据库查询文档列表，同时补充文件存储中的 total_chunks（过渡期兼容）
    db = SessionLocal()
    try:
        docs = db.query(Document).order_by(Document.created_at.desc()).all()
        document_list = [
            {
                "doc_id": d.id,
                "filename": d.filename,
                "file_type": d.file_type,
                "status": d.status,
                "parse_method": d.parse_method,
                "char_count": d.char_count,
                "total_chunks": _get_index_value(d.id, "total_chunks", 0),
                "error_message": d.error_message,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "updated_at": d.updated_at.isoformat() if d.updated_at else None,
            }
            for d in docs
        ]
        return {"documents": document_list}
    finally:
        db.close()


@app.get("/documents/{doc_id}")
def get_document_info(doc_id: str):
    # 先从数据库查询元数据
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
    finally:
        db.close()

    # 文件存储中的索引数据作为补充
    index_path = INDEX_DIR / f"{doc_id}.json"
    index_data = {}
    if index_path.exists():
        index_data = json.loads(index_path.read_text(encoding="utf-8"))

    if not doc and not index_data:
        return {"error": "找不到该 doc_id 对应的文档索引"}

    if doc:
        return {
            "doc_id": doc.id,
            "filename": doc.filename,
            "file_path": doc.storage_path,
            "file_type": doc.file_type,
            "status": doc.status,
            "parse_method": doc.parse_method,
            "char_count": doc.char_count,
            "error_message": doc.error_message,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
            "total_chunks": index_data.get("total_chunks", 0),
            "excel_analysis": index_data.get("excel_analysis"),
            "chart_paths": index_data.get("chart_paths", []),
        }

    # 仅存在于文件存储中的文档（旧数据）
    return {
        "doc_id": index_data["doc_id"],
        "filename": index_data["filename"],
        "file_path": index_data["file_path"],
        "file_type": index_data.get("file_type"),
        "status": "unknown",
        "parse_method": "unknown",
        "char_count": index_data["total_chars"],
        "total_chunks": index_data["total_chunks"],
        "excel_analysis": index_data.get("excel_analysis"),
        "chart_paths": index_data.get("chart_paths", []),
    }


@app.get("/documents/{doc_id}/status")
def get_document_status(doc_id: str):
    """查询文档处理状态。"""
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
    finally:
        db.close()

    if not doc:
        raise DocumentNotFoundError(doc_id)

    return DocumentStatusOut(
        doc_id=doc.id,
        filename=doc.filename,
        status=doc.status,
        parse_method=doc.parse_method,
        char_count=doc.char_count,
        error_message=doc.error_message,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@app.post("/excel/analyze")
async def analyze_excel_api(file: UploadFile = File(...)):
    doc_id = str(uuid.uuid4())

    original_filename = file.filename or "unknown_excel"
    suffix = Path(original_filename).suffix.lower()

    if suffix not in [".xlsx", ".xls"]:
        return {"error": "请上传 .xlsx 或 .xls 文件"}

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
        "chart_paths": chart_paths,
    }


@app.get("/memory")
def get_memory():
    return load_memory()


@app.post("/memory")
def update_user_memory(request: MemoryUpdateRequest):
    memory = update_memory(request.key, request.value)

    return {"message": "记忆更新成功", "memory": memory}


@app.post("/compare")
def compare_documents(request: CompareRequest):
    if len(request.doc_ids) < 2:
        return {"error": "至少需要传入两个 doc_id 才能进行多文档对比"}

    try:
        contexts = build_multi_doc_context(request.doc_ids, max_chunks_per_doc=3)
    except Exception as e:
        return {"error": "构建多文档上下文失败", "detail": str(e)}

    answer = ask_llm(request.question, contexts)

    add_history("compare", f"对比文档：{', '.join(request.doc_ids)}")

    return {
        "doc_ids": request.doc_ids,
        "question": request.question,
        "answer": answer,
        "contexts": contexts,
    }
