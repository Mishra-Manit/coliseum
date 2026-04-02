"""rename title to market_title

Revision ID: 466b053e2596
Revises: 0001
Create Date: 2026-04-02 16:51:28.163041

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '466b053e2596'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('opportunities', 'title', new_column_name='market_title')


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('opportunities', 'market_title', new_column_name='title')
