"""Exa AI service exceptions."""

from coliseum.services.exceptions import ServiceAPIError


class ExaAPIError(ServiceAPIError):
    """Base exception for Exa API errors."""
    pass


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
