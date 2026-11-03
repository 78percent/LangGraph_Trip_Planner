"""Errors with safe, user-readable messages (never forward credential-bearing URLs)."""

#  继承自 Python 内置的 Exception，所以它能像普通异常一样被 raise、被 except 捕获、带上 traceback。
class ServiceError(Exception):  # 项目自己定义的一种异常, FastAPI 可以把它转换成 HTTP 错误响应
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)       # message：错误描述，最终会展示给调用方或用户
        self.status_code = status_code  # status_code：默认 502，允许调用方覆盖。502 是 HTTP 里的 Bad Gateway，语义正是「网关/代理从上游服务拿不到有效响应」——和高德接口调用失败的场景完全吻合。

"""
httpx 的底层异常
        ↓
ServiceError
        ↓
项目统一处理
        ↓
用户看到安全、可理解的提示.

ServiceError 表示的是意料之中的外部依赖失败：
高德挂了、网络断了、返回格式不对。这类错误不需要修代码，
只需要给用户一个友好提示。用独立类型标记，外层就能精准处理。
"""