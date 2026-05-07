"""结构化日志系统。

实现方式：
- 使用 contextvars 在请求链路中透传 request_id，避免层层传参
- StructuredJsonFormatter 将每行日志输出为 JSON，便于日志收集系统解析
- log_event 封装 extra 参数传递，统一结构化字段的写入入口
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from contextvars import ContextVar

# ── request_id 上下文变量 ──
# 由中间件在每个请求入口设置，日志格式化器自动读取，
# 实现"一次设置、全局生效"，无需在每个函数中显式传递。
_request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """获取当前请求的 request_id"""
    return _request_id_ctx.get()


def set_request_id(request_id: str) -> str:
    """设置当前请求的 request_id，返回 token 供后续 reset 使用"""
    token = _request_id_ctx.set(request_id)
    return token


def reset_request_id(token) -> None:
    """恢复 request_id 至之前的值"""
    _request_id_ctx.reset(token)


# ── 结构化字段键名列表 ──
# 与 log_event 的 extra 参数一一对应，在 formatter 中统一读取
_STRUCTURED_FIELDS = [
    "operation",
    "duration_ms",
    "user_id",
    "file_id",
    "error_detail",
]


class StructuredJsonFormatter(logging.Formatter):
    """JSON 行日志格式化器。

    将每行日志格式化为包含所有结构化字段的 JSON 对象，
    缺省字段输出 null，确保日志收集系统（如 Loki、ELK）的字段一致性。

    设计决策：固定字段由 formatter 硬编码输出；extra_fields
    通过 log_event 在 LogRecord 上注册 _extra_keys 追踪。
    不使用 dir(record) 扫描，避免意外泄露 LogRecord 内部属性。
    """

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }

        for field in _STRUCTURED_FIELDS:
            entry[field] = getattr(record, field, None)

        entry["request_id"] = getattr(record, "request_id", None) or get_request_id() or None

        # 仅输出 log_event 明确传递的额外字段，不扫描 LogRecord 所有属性
        extra_keys = getattr(record, "_extra_keys", None)
        if extra_keys:
            for key in extra_keys:
                if key not in entry:
                    entry[key] = getattr(record, key, None)

        return json.dumps(entry, ensure_ascii=False, default=str)


def setup_logging(log_dir: str = "logs", log_file: str = "app.log") -> None:
    """配置结构化日志系统。

    同时输出到控制台和文件，均为 JSON 行格式。
    幂等操作：每次调用会清空已有 handler 避免重复。
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 清空已有 handler，避免 reload 时重复
    root_logger.handlers.clear()

    formatter = StructuredJsonFormatter()

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 文件输出
    file_handler = logging.FileHandler(
        str(log_path / log_file), encoding="utf-8", mode="a"
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)


def log_event(
    logger: logging.Logger,
    level: int,
    message: str,
    operation: Optional[str] = None,
    duration_ms: Optional[float] = None,
    user_id: Optional[str] = None,
    file_id: Optional[str] = None,
    error_detail: Optional[str] = None,
    exc_info: bool = False,
    extra_fields: Optional[dict] = None,
) -> None:
    """结构化日志记录函数。

    通过 extra 参数传递结构化字段，StructuredJsonFormatter
    在格式化时统一序列化为 JSON 中的对应字段。

    extra_fields: 额外字段字典，会自动合并到 JSON 输出中，
                  适合记录 parse_method、text_length 等业务相关字段。
    """
    extra = {
        "operation": operation,
        "duration_ms": duration_ms,
        "user_id": user_id,
        "file_id": file_id,
        "error_detail": error_detail,
    }
    extra["_extra_keys"] = list(extra.keys())
    if extra_fields:
        extra.update(extra_fields)
        # 将 extra_fields 中的键也加入追踪列表
        extra["_extra_keys"].extend(extra_fields.keys())

    logger.log(level, message, extra=extra, exc_info=exc_info)
