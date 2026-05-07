"""业务异常层次结构。

设计决策：所有自定义异常继承 AppException 基类，
全局 exception_handler 通过 isinstance 判断异常类型，
新增异常子类时无需改动全局处理逻辑。
"""


class AppException(Exception):
    """业务异常基类。

    属性：
        code: 业务状态码（非 HTTP 状态码），用于前端精细化处理
        message: 人类可读的错误描述
        http_status_code: 对应的 HTTP 状态码
    """

    def __init__(self, code: int, message: str, http_status_code: int = 400):
        self.code = code
        self.message = message
        self.http_status_code = http_status_code
        super().__init__(self.message)


# ── 文件/文档相关异常（code 100x） ──


class FileTypeNotSupportedError(AppException):
    """不支持的文件类型"""

    def __init__(self, file_type: str = ""):
        msg = f"暂不支持该文件类型：{file_type}" if file_type else "暂不支持该文件类型"
        super().__init__(code=1001, message=msg, http_status_code=400)


class FileParseError(AppException):
    """文档解析失败"""

    def __init__(self, message: str = "文档解析失败", detail: str = ""):
        full_msg = f"{message}：{detail}" if detail else message
        super().__init__(code=1002, message=full_msg, http_status_code=400)


class DocumentNotFoundError(AppException):
    """文档索引不存在"""

    def __init__(self, doc_id: str = ""):
        msg = f"找不到该文档：{doc_id}" if doc_id else "找不到该文档"
        super().__init__(code=1003, message=msg, http_status_code=404)


# ── OCR 相关异常（code 200x） ──


class OCRException(AppException):
    """OCR 识别失败"""

    def __init__(self, message: str = "OCR 识别失败"):
        super().__init__(code=2001, message=message, http_status_code=500)


# ── LLM 相关异常（code 300x） ──


class LLMException(AppException):
    """LLM 调用失败"""

    def __init__(self, message: str = "LLM 调用失败"):
        super().__init__(code=3001, message=message, http_status_code=502)


class LLMConfigurationError(AppException):
    """LLM 配置缺失或无效"""

    def __init__(self, message: str = "LLM 配置错误"):
        super().__init__(code=3002, message=message, http_status_code=500)
