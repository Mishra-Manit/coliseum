"""Shared base exceptions for all external service clients."""


class ServiceAPIError(Exception):
    """Base exception for all external service API errors."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code
