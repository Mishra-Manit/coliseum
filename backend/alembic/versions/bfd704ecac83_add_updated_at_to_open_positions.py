"""add updated_at to open_positions

Revision ID: bfd704ecac83
Revises: 42f8ba0e3ee1
Create Date: 2026-04-06 19:24:46.187884

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'bfd704ecac83'
down_revision: Union[str, Sequence[str], None] = '42f8ba0e3ee1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_table("portfolio_snapshots")
    op.add_column(
        "open_positions",
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("open_positions", "updated_at")
    op.create_table(
        "portfolio_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("total_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("cash_balance", sa.Numeric(12, 2), nullable=False),
        sa.Column("positions_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("open_positions", sa.Integer(), nullable=False),
        sa.Column("realized_pnl", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "snapshot_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
