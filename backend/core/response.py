from typing import Any, Optional

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    """统一响应模型。

    所有 API 响应（包括正常和异常）都使用此结构返回，
    保证前后端交互的格式一致性。
    """

    code: int = Field(default=0, description="业务状态码，0 表示成功，非 0 表示各类错误")
    message: str = Field(default="ok", description="提示信息")
    data: Any = Field(default=None, description="响应数据")
    request_id: str = Field(default="", description="请求唯一标识，用于链路追踪")

    @classmethod
    def success(
        cls, data: Any = None, message: str = "ok", request_id: str = ""
    ) -> "ApiResponse":
        """构造成功响应。"""
        return cls(code=0, message=message, data=data, request_id=request_id)

    @classmethod
    def error(
        cls,
        code: int,
        message: str,
        request_id: str = "",
        data: Any = None,
    ) -> "ApiResponse":
        """构造错误响应。"""
        return cls(code=code, message=message, data=data, request_id=request_id)
