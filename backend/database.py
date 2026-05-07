"""数据库基础设施。

创建 engine、SessionLocal、Base declarative_base。
get_db() 提供 FastAPI 依赖注入，init_db() 用于启动时建表。
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

DATABASE_URL = os.getenv("DOCFLOW_DATABASE_URL") or os.getenv("DATABASE_URL", "sqlite:///./storage/docflow.db")

# SQLite 需要 check_same_thread=False 以支持 FastAPI 多线程
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI 依赖注入：每个请求获取一个数据库会话，请求结束后关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """创建所有表（幂等，CREATE TABLE IF NOT EXISTS）。"""
    Base.metadata.create_all(bind=engine)
