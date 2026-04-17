"""drop run_cycles table

Revision ID: ce1a2b3d4e5f
Revises: e472f9c1e70e
Create Date: 2026-04-17 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY, JSONB


# revision identifiers, used by Alembic.
revision: str = "ce1a2b3d4e5f"
down_revision: Union[str, Sequence[str], None] = "b2aab9d0dc73"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop the run_cycles telemetry table."""
    op.drop_table("run_cycles")


def downgrade() -> None:
    """Recreate the run_cycles table."""
    op.create_table(
        "run_cycles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cycle_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column(
            "guardian_synced",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "guardian_closed",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "scout_scanned",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "scout_found",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("analyst_results", JSONB(), nullable=True),
        sa.Column("trader_results", JSONB(), nullable=True),
        sa.Column("cash_balance", sa.Numeric(12, 2), nullable=True),
        sa.Column("positions_value", sa.Numeric(12, 2), nullable=True),
        sa.Column("total_value", sa.Numeric(12, 2), nullable=True),
        sa.Column("open_positions", sa.Integer(), nullable=True),
        sa.Column(
            "errors",
            ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::text[]"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
