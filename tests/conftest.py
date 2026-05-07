"""pytest 配置：测试隔离、LLM mock、临时数据库。"""

import os
import tempfile
from pathlib import Path

# ── 在导入任何业务模块前，设置环境变量 ──
# database.py 在 import 时读取该变量创建 engine/SessionLocal
_TMP_DIR = Path(tempfile.mkdtemp())
os.environ["DOCFLOW_DATABASE_URL"] = f"sqlite:///{_TMP_DIR / 'test.db'}"
os.environ["OCR_ENABLED"] = "false"

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import engine
from backend.models import Base


@pytest.fixture(scope="session", autouse=True)
def _session_cleanup():
    yield
    engine.dispose()
    import shutil

    shutil.rmtree(_TMP_DIR, ignore_errors=True)


@pytest.fixture(autouse=True)
def _setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _mock_llm(monkeypatch):
    monkeypatch.setattr(
        "backend.main.ask_llm",
        lambda q, ctx: "这是一段 mock 回答，用于测试问答记录写入。",
    )
    monkeypatch.setattr(
        "backend.main.summarize_text",
        lambda f, t, **kw: "mock 摘要内容",
    )
    monkeypatch.setattr(
        "backend.main.summarize_text_stream",
        lambda f, t, **kw: iter(["mock 摘要内容"]),
    )


@pytest.fixture(autouse=True)
def _storage_dirs(monkeypatch, tmp_path):
    upload_dir = tmp_path / "uploads"
    index_dir = tmp_path / "index"
    output_dir = tmp_path / "outputs"
    vector_index_dir = tmp_path / "vector_index"
    upload_dir.mkdir()
    index_dir.mkdir()
    output_dir.mkdir()
    vector_index_dir.mkdir()
    monkeypatch.setattr("backend.main.UPLOAD_DIR", upload_dir)
    monkeypatch.setattr("backend.main.INDEX_DIR", index_dir)
    monkeypatch.setattr("backend.main.OUTPUT_DIR", output_dir)
    monkeypatch.setattr("backend.vector_store.VECTOR_INDEX_DIR", vector_index_dir)


@pytest.fixture
def client():
    return TestClient(app)
