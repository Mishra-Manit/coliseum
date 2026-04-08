"""Data models for the X Sentiment agent."""

from enum import StrEnum

from pydantic import BaseModel, Field


class Sentiment(StrEnum):
    """How X sentiment relates to the market's expected resolution."""

    CONFIRMS_RESOLUTION = "CONFIRMS_RESOLUTION"
    CONTRADICTS_RESOLUTION = "CONTRADICTS_RESOLUTION"
    MIXED = "MIXED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class KeyPost(BaseModel):
    """A notable X post surfaced during sentiment analysis."""

    summary: str = Field(description="One-sentence summary of the post content")
    author_context: str = Field(description="Who posted it — role, follower count, relevance")
    engagement: str = Field(description="Engagement metrics — likes, reposts, replies")


class XSentimentOutput(BaseModel):
    """Structured output from the X Sentiment agent."""

    sentiment: Sentiment = Field(
        description="Whether X discussion confirms or contradicts the market's expected resolution"
    )
    analysis: str = Field(
        description="Factual synthesis of what X posts say about this topic, 100-200 words"
    )
    key_posts: list[KeyPost] = Field(
        description="2-5 notable posts with engagement context",
        min_length=0,
    )

    def to_markdown(self) -> str:
        """Render as a markdown section for appending to research synthesis."""
        lines = [
            "*Note: This is unverified public opinion from social media, not factual evidence. "
            "Treat as a supplementary signal only. Do not base trade decisions solely on X sentiment.*",
            "",
            f"**X Sentiment:** {self.sentiment.value}",
            "",
            self.analysis,
        ]
        if self.key_posts:
            lines.append("")
            lines.append("**Notable Posts:**")
            for post in self.key_posts:
                lines.append(f"- {post.summary} ({post.author_context}, {post.engagement})")
        return "\n".join(lines)
