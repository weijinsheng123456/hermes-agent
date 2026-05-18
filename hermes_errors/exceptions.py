"""Hermes Agent 统一异常处理系统

版本：1.0
创建日期：2026-04-22
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any


class HermesError(Exception):
    """所有 Hermes 自定义异常的基类"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于 JSON 序列化"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp
        }
    
    def to_json(self) -> str:
        """转换为 JSON 字符串，用于工具返回值"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


# ========== 工具相关异常 ==========

class ToolError(HermesError):
    """工具执行相关的基类异常"""
    pass


class ToolUnavailableError(ToolError):
    """工具不可用 - 缺少 API key 或环境未配置"""
    
    def __init__(self, tool_name: str, reason: str = "未知原因"):
        super().__init__(
            message=f"工具 '{tool_name}' 不可用",
            details={"tool": tool_name, "reason": reason}
        )


class ToolExecutionError(ToolError):
    """工具执行失败 - 参数错误或外部服务失败"""
    
    def __init__(self, tool_name: str, message: str, original_error: Optional[Exception] = None):
        details = {"tool": tool_name}
        if original_error:
            details["original_error"] = str(original_error)
            details["original_error_type"] = type(original_error).__name__
        super().__init__(message=message, details=details)


class ToolNotFoundError(ToolError):
    """工具未找到"""
    
    def __init__(self, tool_name: str):
        super().__init__(
            message=f"未找到工具 '{tool_name}'",
            details={"tool": tool_name}
        )


class ToolTimeoutError(ToolError):
    """工具执行超时"""
    
    def __init__(self, tool_name: str, timeout_seconds: int):
        super().__init__(
            message=f"工具 '{tool_name}' 执行超时 ({timeout_seconds}秒)",
            details={"tool": tool_name, "timeout": timeout_seconds}
        )


# ========== API 相关异常 ==========

class APIError(HermesError):
    """API 调用相关的基类异常"""
    pass


class APIConnectionError(APIError):
    """API 连接失败 - 网络问题或服务不可用"""
    
    def __init__(self, provider: str, url: str, reason: str = "连接失败"):
        super().__init__(
            message=f"无法连接到 {provider} API",
            details={"provider": provider, "url": url, "reason": reason}
        )


class APIAuthenticationError(APIError):
    """API 认证失败 - API key 无效或过期"""
    
    def __init__(self, provider: str, reason: str = "认证失败"):
        super().__init__(
            message=f"{provider} API 认证失败",
            details={"provider": provider, "reason": reason}
        )


class APIRateLimitError(APIError):
    """API 频率限制 - 配额耗尽"""
    
    def __init__(self, provider: str, retry_after: Optional[int] = None):
        details = {"provider": provider}
        if retry_after:
            details["retry_after_seconds"] = retry_after
        super().__init__(
            message=f"{provider} API 频率限制已耗尽",
            details=details
        )


class APITimeoutError(APIError):
    """API 请求超时"""
    
    def __init__(self, provider: str, timeout_seconds: int):
        super().__init__(
            message=f"{provider} API 请求超时 ({timeout_seconds}秒)",
            details={"provider": provider, "timeout": timeout_seconds}
        )


# ========== 会话相关异常 ==========

class SessionError(HermesError):
    """会话管理相关的基类异常"""
    pass


class SessionNotFoundError(SessionError):
    """会话未找到"""
    
    def __init__(self, session_id: str):
        super().__init__(
            message=f"未找到会话 '{session_id}'",
            details={"session_id": session_id}
        )


class SessionLoadError(SessionError):
    """会话加载失败"""
    
    def __init__(self, session_id: str, reason: str = "加载失败"):
        super().__init__(
            message=f"无法加载会话 '{session_id}'",
            details={"session_id": session_id, "reason": reason}
        )


# ========== 配置相关异常 ==========

class ConfigError(HermesError):
    """配置相关的基类异常"""
    pass


class ConfigNotFoundError(ConfigError):
    """配置文件未找到"""
    
    def __init__(self, config_path: str):
        super().__init__(
            message=f"配置文件未找到",
            details={"path": config_path}
        )


class ConfigValidationError(ConfigError):
    """配置验证失败"""
    
    def __init__(self, field: str, message: str):
        super().__init__(
            message=f"配置验证失败：{field} - {message}",
            details={"field": field}
        )


# ========== 权限相关异常 ==========

class PermissionError(HermesError):
    """权限相关的基类异常"""
    pass


class ApprovalRequiredError(PermissionError):
    """需要用户审批 - 危险操作"""
    
    def __init__(self, operation: str, reason: str = "危险操作"):
        super().__init__(
            message=f"操作需要审批：{operation}",
            details={"operation": operation, "reason": reason}
        )


class AccessDeniedError(PermissionError):
    """访问被拒绝"""
    
    def __init__(self, resource: str, reason: str = "权限不足"):
        super().__init__(
            message=f"访问被拒绝：{resource}",
            details={"resource": resource, "reason": reason}
        )


# ========== 系统相关异常 ==========

class SystemError(HermesError):
    """系统相关的基类异常"""
    pass


class ResourceExhaustedError(SystemError):
    """资源耗尽 - 内存、磁盘、连接数等"""
    
    def __init__(self, resource_type: str, current_usage: str = "未知"):
        super().__init__(
            message=f"资源耗尽：{resource_type}",
            details={"resource": resource_type, "usage": current_usage}
        )


class DependencyError(SystemError):
    """依赖项缺失或版本不兼容"""
    
    def __init__(self, dependency: str, required_version: Optional[str] = None):
        details = {"dependency": dependency}
        if required_version:
            details["required_version"] = required_version
        super().__init__(
            message=f"依赖项问题：{dependency}",
            details=details
        )


# ========== 便捷函数 ==========

def safe_execute(func, *args, **kwargs):
    """安全执行函数，捕获所有异常并返回标准格式
    
    Usage:
        result = safe_execute(my_function, arg1, arg2)
        if result["success"]:
            process(result["data"])
        else:
            handle_error(result["error"])
    """
    try:
        result = func(*args, **kwargs)
        return {"success": True, "data": result}
    except HermesError as e:
        return {"success": False, "error": e.to_dict()}
    except Exception as e:
        return {
            "success": False,
            "error": {
                "error": "UnexpectedError",
                "message": str(e),
                "details": {"type": type(e).__name__},
                "timestamp": datetime.now().isoformat()
            }
        }


def raise_from_tool_exception(tool_name: str, exception: Exception) -> ToolExecutionError:
    """将普通异常转换为工具执行异常"""
    return ToolExecutionError(
        tool_name=tool_name,
        message=f"工具执行失败：{str(exception)}",
        original_error=exception
    )


# 导出所有异常类
__all__ = [
    "HermesError",
    "ToolError", "ToolUnavailableError", "ToolExecutionError", 
    "ToolNotFoundError", "ToolTimeoutError",
    "APIError", "APIConnectionError", "APIAuthenticationError",
    "APIRateLimitError", "APITimeoutError",
    "SessionError", "SessionNotFoundError", "SessionLoadError",
    "ConfigError", "ConfigNotFoundError", "ConfigValidationError",
    "PermissionError", "ApprovalRequiredError", "AccessDeniedError",
    "SystemError", "ResourceExhaustedError", "DependencyError",
    "safe_execute", "raise_from_tool_exception"
]
