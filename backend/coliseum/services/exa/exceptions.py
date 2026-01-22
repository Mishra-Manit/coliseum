"""Custom exceptions for Exa AI service."""


class ExaAPIError(Exception):
    """Base exception for Exa API errors."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class ExaAuthError(ExaAPIError):
    """Authentication failed (401)."""

    pass


class ExaRateLimitError(ExaAPIError):
    """Rate limit exceeded (429)."""

    pass


class ExaBadRequestError(ExaAPIError):
    """Invalid request parameters (400)."""

    pass


class ExaServerError(ExaAPIError):
    """Server-side error (5xx)."""

    pass
