"""Errors with safe, user-readable messages (never forward credential-bearing URLs)."""


class ServiceError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code
