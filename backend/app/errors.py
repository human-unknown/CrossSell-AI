"""
CrossSell AI — 标准化错误体系
===============================
所有业务异常统一继承 AppError，由 global_exception_handler 统一捕获，
返回格式：{"detail": "...", "error_code": "TASK_NOT_FOUND", "status_code": 404}
"""

from typing import Optional


class AppError(Exception):
    """应用异常基类"""

    error_code: str = "INTERNAL_ERROR"
    status_code: int = 500
    message: str = "An unexpected error occurred"

    def __init__(self, message: Optional[str] = None, detail: Optional[str] = None):
        self.message = message or self.message
        self.detail = detail  # 额外调试信息，不暴露给前端
        super().__init__(self.message)


# ------------------------------------------------------------------
# 4xx 客户端错误
# ------------------------------------------------------------------


class ValidationError(AppError):
    """400 — 请求参数校验失败"""
    error_code = "VALIDATION_ERROR"
    status_code = 400
    message = "Request validation failed"


class TaskNotFoundError(AppError):
    """404 — 任务不存在"""
    error_code = "TASK_NOT_FOUND"
    status_code = 404
    message = "Task not found"


class TaskNotReadyError(AppError):
    """425 — 任务尚未完成，结果不可用"""
    error_code = "TASK_NOT_READY"
    status_code = 425
    message = "Task result not ready yet"


class RateLimitError(AppError):
    """429 — 请求频率超限"""
    error_code = "RATE_LIMIT_EXCEEDED"
    status_code = 429
    message = "Too many requests, please try again later"


# ------------------------------------------------------------------
# 5xx 服务端错误
# ------------------------------------------------------------------


class AIServiceError(AppError):
    """502 — AI 服务调用失败（区别于 500 内部错误）"""
    error_code = "AI_SERVICE_ERROR"
    status_code = 502
    message = "AI service temporarily unavailable"


class DatabaseError(AppError):
    """503 — 数据库操作失败"""
    error_code = "DATABASE_ERROR"
    status_code = 503
    message = "Database operation failed"
