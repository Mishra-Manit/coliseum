"""add check constraint on learnings category

Revision ID: 42f8ba0e3ee1
Revises: 466b053e2596
Create Date: 2026-04-02 19:28:57.942088

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42f8ba0e3ee1'
down_revision: Union[str, Sequence[str], None] = '466b053e2596'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        "ck_learnings_category",
        "learnings",
        "category IN ('Market Patterns', 'Execution Patterns', 'Error Patterns')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("ck_learnings_category", "learnings")
