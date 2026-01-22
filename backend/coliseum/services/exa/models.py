"""Type-safe Pydantic models for Exa AI SDK responses."""

from pydantic import BaseModel


class ExaCitation(BaseModel):
    """Citation in an answer response."""

    url: str
    title: str
    text: str | None = None


class ExaAnswerResponse(BaseModel):
    """Response from answer operation."""

    answer: str
    citations: list[ExaCitation]
    query: str
