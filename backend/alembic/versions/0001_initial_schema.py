"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-02 15:08:02.316393

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY, JSONB


# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "opportunities",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("market_ticker", sa.Text(), nullable=False),
        sa.Column("event_ticker", sa.Text(), nullable=False),
        sa.Column("event_title", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("subtitle", sa.Text(), nullable=True),
        sa.Column("yes_price", sa.Numeric(5, 4), nullable=False),
        sa.Column("no_price", sa.Numeric(5, 4), nullable=False),
        sa.Column("close_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("outcome_status", sa.Text(), nullable=False),
        sa.Column("risk_level", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=True),
        sa.Column("trader_decision", sa.Text(), nullable=True),
        sa.Column("research_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recommendation_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_stage", sa.Text(), nullable=True),
        sa.Column("failure_error", sa.Text(), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paper", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "opportunity_analysis",
        sa.Column("opportunity_id", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("resolution_source", sa.Text(), nullable=True),
        sa.Column(
            "evidence_bullets",
            ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::text[]"),
        ),
        sa.Column(
            "remaining_risks",
            ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::text[]"),
        ),
        sa.Column(
            "scout_sources",
            ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::text[]"),
        ),
        sa.Column("research_synthesis", sa.Text(), nullable=True),
        sa.Column("trader_tldr", sa.Text(), nullable=True),
        sa.Column("research_duration_seconds", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.PrimaryKeyConstraint("opportunity_id"),
    )

    op.create_table(
        "open_positions",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("market_ticker", sa.Text(), nullable=False),
        sa.Column("side", sa.Text(), nullable=False),
        sa.Column("contracts", sa.Integer(), nullable=False),
        sa.Column("average_entry", sa.Numeric(5, 4), nullable=False),
        sa.Column("current_price", sa.Numeric(5, 4), nullable=False),
        sa.Column("opportunity_id", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "closed_positions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("market_ticker", sa.Text(), nullable=False),
        sa.Column("side", sa.Text(), nullable=False),
        sa.Column("contracts", sa.Integer(), nullable=False),
        sa.Column("entry_price", sa.Numeric(5, 4), nullable=False),
        sa.Column("exit_price", sa.Numeric(5, 4), nullable=False),
        sa.Column("pnl", sa.Numeric(12, 2), nullable=False),
        sa.Column("opportunity_id", sa.Text(), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("entry_rationale", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "trades",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("position_id", sa.Text(), nullable=True),
        sa.Column("opportunity_id", sa.Text(), nullable=True),
        sa.Column("market_ticker", sa.Text(), nullable=False),
        sa.Column("side", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("contracts", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(5, 4), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("paper", sa.Boolean(), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "trade_closes",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("opportunity_id", sa.Text(), nullable=True),
        sa.Column("market_ticker", sa.Text(), nullable=False),
        sa.Column("side", sa.Text(), nullable=False),
        sa.Column("contracts", sa.Integer(), nullable=False),
        sa.Column("entry_price", sa.Numeric(5, 4), nullable=False),
        sa.Column("exit_price", sa.Numeric(5, 4), nullable=False),
        sa.Column("pnl", sa.Numeric(12, 2), nullable=False),
        sa.Column("entry_rationale", sa.Text(), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "portfolio_state",
        sa.Column("id", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("cash_balance", sa.Numeric(12, 2), nullable=False),
        sa.Column("positions_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_value", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("id = 1", name="ck_portfolio_state_singleton"),
        sa.PrimaryKeyConstraint("id"),
    )

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
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "seen_tickers",
        sa.Column("ticker", sa.Text(), nullable=False),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("ticker"),
    )

    op.create_table(
        "decisions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("opportunity_id", sa.Text(), nullable=True),
        sa.Column("ticker", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("price", sa.Numeric(5, 4), nullable=False),
        sa.Column("contracts", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column("tldr", sa.Text(), nullable=True),
        sa.Column("execution_status", sa.Text(), nullable=False),
        sa.Column("outcome", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

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

    op.create_table(
        "learnings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("learnings")
    op.drop_table("run_cycles")
    op.drop_table("decisions")
    op.drop_table("seen_tickers")
    op.drop_table("portfolio_snapshots")
    op.drop_table("portfolio_state")
    op.drop_table("trade_closes")
    op.drop_table("trades")
    op.drop_table("closed_positions")
    op.drop_table("open_positions")
    op.drop_table("opportunity_analysis")
    op.drop_table("opportunities")
