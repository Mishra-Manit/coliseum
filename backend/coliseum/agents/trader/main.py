"""Trader Agent: Final decision-maker and trade executor."""

import asyncio
import logging
from contextlib import AsyncExitStack
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

import logfire

from pydantic_ai import Agent, RunContext

from coliseum.agents.agent_factory import AgentFactory, create_agent
from coliseum.agents.trader.models import (
    OrderResult,
    TraderDependencies,
    TraderOutput,
)
from coliseum.agents.trader.prompts import (
    build_trader_system_prompt,
    build_trader_prompt,
)
from coliseum.config import Settings, get_settings
from coliseum.services.kalshi.client import KalshiClient
from coliseum.services.kalshi.config import KalshiConfig
from coliseum.services.telegram import TelegramClient, create_telegram_client
from coliseum.storage.files import (
    OpportunitySignal,
    TradeExecution,
    find_opportunity_file_by_id,
    generate_trade_id,
    log_trade,
    update_opportunity_frontmatter,
)
from coliseum.memory.decisions import DecisionEntry, log_decision
from coliseum.services.supabase.repositories.opportunities import (
    load_opportunity_from_db,
    get_opportunity_body_from_db,
    update_opportunity_trader_decision,
)
from coliseum.services.supabase.repositories.trades import save_trade_to_db
from coliseum.services.supabase.repositories.decisions import save_decision_to_db
from coliseum.services.supabase.repositories.portfolio import (
    load_state_from_db,
    update_portfolio_after_trade_in_db,
)
from coliseum.storage.state import (
    PortfolioState,
    PortfolioStats,
    Position,
    save_state,
)

logger = logging.getLogger(__name__)


def _create_agent(settings: Settings) -> Agent[TraderDependencies, TraderOutput]:
    """Create the Trader agent."""
    return create_agent(
        prompt=build_trader_system_prompt(settings),
        output_type=TraderOutput,
        deps_type=TraderDependencies,
        prepend_mechanics=False,
        use_responses_api=False,
    )


def _register_tools(agent: Agent[TraderDependencies, TraderOutput]) -> None:
    """Register tools for the Trader agent."""

    @agent.tool
    async def get_current_market_price(
        ctx: RunContext[TraderDependencies],
        ticker: str,
    ) -> dict:
        """Fetch live Kalshi orderbook prices to confirm YES or NO is still 92-96%."""
        client = ctx.deps.kalshi_client
        market = await client.get_market(ticker)
        if market.yes_ask:
            yes_price_decimal = market.yes_ask / 100
        else:
            yes_price_decimal = None

        if market.no_ask:
            no_price_decimal = market.no_ask / 100
        else:
            no_price_decimal = None

        return {
            "ticker": ticker,
            "yes_ask": market.yes_ask,
            "yes_price_decimal": yes_price_decimal,
            "no_ask": market.no_ask,
            "no_price_decimal": no_price_decimal,
        }


def _calc_fill_price(taker_cost: float, maker_cost: float, fill_count: int, fallback_cents: int) -> float:
    """Calculate average fill price in decimal (0-1)."""
    if fill_count > 0:
        return (taker_cost + maker_cost) / (fill_count * 100)
    return fallback_cents / 100


async def execute_working_order(
    client: KalshiClient,
    ticker: str,
    side: Literal["yes", "no"],
    contracts: int,
    initial_price_cents: int,
    config: Settings,
) -> OrderResult:
    """Execute limit order with place → wait → reprice → cancel strategy to avoid market orders."""
    client_order_id = f"trader_{uuid4().hex[:8]}"
    current_price = initial_price_cents
    max_attempts = config.execution.max_reprice_attempts + 1  # +1 for initial placement
    check_interval = config.execution.order_check_interval_seconds
    reprice_aggression_cents = int(config.execution.reprice_aggression * 100)

    order_id: str | None = None

    for attempt in range(max_attempts):
        try:
            # Place or reprice order
            if attempt == 0:
                # Initial placement
                if side == "yes":
                    order = await client.place_order(
                        ticker=ticker,
                        side="yes",
                        action="buy",
                        count=contracts,
                        yes_price=current_price,
                        client_order_id=client_order_id,
                    )
                else:
                    order = await client.place_order(
                        ticker=ticker,
                        side="no",
                        action="buy",
                        count=contracts,
                        no_price=current_price,
                        client_order_id=client_order_id,
                    )
                order_id = order.order_id
                logger.info("Placed order %s: %d %s @ %d¢", order_id, contracts, side, current_price)
            else:
                # Reprice existing order
                order = await client.amend_order(order_id, price=current_price)
                logger.info("Repriced order %s to %d¢ (attempt %d)", order_id, current_price, attempt)

            # Wait for fill
            await asyncio.sleep(check_interval)

            # Check status
            order = await client.get_order_status(order_id)

            if order.is_filled:
                # Fully filled — fall back to `contracts` if Kalshi omits fill counts
                if order.fill_count > 0:
                    actual_fill_count = order.fill_count
                else:
                    actual_fill_count = contracts
                fill_price_decimal = _calc_fill_price(
                    order.taker_fill_cost, order.maker_fill_cost, order.fill_count, current_price
                )
                total_cost = fill_price_decimal * actual_fill_count

                return OrderResult(
                    order_id=order_id,
                    fill_price=fill_price_decimal,
                    contracts_filled=actual_fill_count,
                    total_cost_usd=total_cost,
                    status="filled",
                )

            # Check if partial fill is worth keeping
            if contracts > 0:
                fill_pct = order.fill_count / contracts
            else:
                fill_pct = 0.0
            if fill_pct >= config.execution.min_fill_pct_to_keep:
                fill_price_decimal = _calc_fill_price(
                    order.taker_fill_cost, order.maker_fill_cost, order.fill_count, current_price
                )
                total_cost = (order.taker_fill_cost + order.maker_fill_cost) / 100

                await client.cancel_order(order_id)
                logger.info("Keeping partial fill: %d/%d", order.fill_count, contracts)

                return OrderResult(
                    order_id=order_id,
                    fill_price=fill_price_decimal,
                    contracts_filled=order.fill_count,
                    total_cost_usd=total_cost,
                    status="partial",
                )

            # Not filled yet, reprice if we have attempts left
            if attempt < max_attempts - 1:
                # Increase price by aggression amount
                current_price = min(99, current_price + reprice_aggression_cents)
                logger.info("Repricing to %d¢ for next attempt", current_price)
            else:
                # Out of attempts, cancel
                await client.cancel_order(order_id)
                logger.info("Cancelled order %s after %d attempts", order_id, max_attempts)

                # Final poll — catch any fills that landed during the cancel window
                refreshed = None
                try:
                    refreshed = await client.get_order_status(order_id)
                except Exception as exc:
                    logger.warning("Final status poll failed for %s: %s", order_id, exc)

                if refreshed is not None:
                    order = refreshed

                # Return partial fill if any
                if order.fill_count > 0:
                    fill_price_decimal = _calc_fill_price(
                        order.taker_fill_cost, order.maker_fill_cost, order.fill_count, current_price
                    )
                    total_cost = (order.taker_fill_cost + order.maker_fill_cost) / 100
                    return OrderResult(
                        order_id=order_id,
                        fill_price=fill_price_decimal,
                        contracts_filled=order.fill_count,
                        total_cost_usd=total_cost,
                        status="partial",
                    )

                return OrderResult(
                    order_id=order_id,
                    status="cancelled",
                )

        except Exception as e:
            logger.error("Error in working order execution: %s", e)
            if order_id:
                try:
                    await client.cancel_order(order_id)
                except Exception:
                    pass
            return OrderResult(
                order_id=order_id,
                status="error",
                error_message=str(e),
            )

    # Should not reach here
    return OrderResult(status="error", error_message="Unexpected end of loop")


_agent_factory: AgentFactory[TraderDependencies, TraderOutput] | None = None


def get_agent(settings: Settings) -> Agent[TraderDependencies, TraderOutput]:
    """Get the singleton Trader agent instance."""
    global _agent_factory
    if _agent_factory is None:
        _agent_factory = AgentFactory(
            create_fn=lambda: _create_agent(settings),
            register_tools_fn=_register_tools,
        )
    return _agent_factory.get_agent()


async def run_trader(
    opportunity_id: str,
    settings: Settings | None = None,
) -> TraderOutput:
    """Execute or reject trade after validating recommendation, checking slippage, and verifying risk limits."""
    if settings is None:
        settings = get_settings()

    opportunity = await load_opportunity_from_db(opportunity_id)

    if not opportunity.recommendation_completed_at:
        raise ValueError(f"Recommendation not completed for {opportunity_id}")

    kalshi_config = KalshiConfig()
    # No auth needed in paper mode — market reads work unauthenticated; execution is skipped
    if settings.trading.paper_mode:
        private_key_pem = ""
    else:
        private_key_pem = settings.get_rsa_private_key()

    with logfire.span("trader", opportunity_id=opportunity_id, ticker=opportunity.market_ticker):
        async with AsyncExitStack() as stack:
            client = await stack.enter_async_context(
                KalshiClient(
                    config=kalshi_config,
                    api_key=settings.kalshi_api_key,
                    private_key_pem=private_key_pem,
                )
            )
            telegram_client = None
            if settings.telegram_send_alerts:
                telegram_client = await stack.enter_async_context(
                    create_telegram_client(
                        bot_token=settings.telegram_bot_token,
                        chat_id=settings.telegram_chat_id,
                    )
                )

            deps = TraderDependencies(
                kalshi_client=client,
                config=settings,
            )

            markdown_body = await get_opportunity_body_from_db(opportunity_id)
            prompt = await build_trader_prompt(opportunity, markdown_body, settings)

            with logfire.span("agent decision", ticker=opportunity.market_ticker):
                agent = get_agent(settings)
                result = await agent.run(prompt, deps=deps)
                output: TraderOutput = result.output
                logfire.info("Decision made", action=output.decision.action)

            if output.decision.action == "REJECT":
                output = output.model_copy(update={"execution_status": "skipped"})
                logfire.info("Trade rejected", reasoning=output.decision.reasoning)
            else:
                if output.decision.action == "EXECUTE_BUY_YES":
                    side = "yes"
                else:
                    side = "no"

                if side == "yes":
                    target_price = opportunity.yes_price
                else:
                    target_price = opportunity.no_price
                try:
                    output = await _execute_trade(
                        client, opportunity, output, side, target_price, settings,
                    )
                except Exception as exc:
                    logfire.error("Trade execution failed", opportunity_id=opportunity_id, error=str(exc))

            # Single atomic frontmatter write after execution_status is finalized
            frontmatter_updates = {
                "trader_decision": output.decision.action,
                "trader_tldr": output.tldr,
            }
            if output.decision.action == "REJECT":
                frontmatter_updates["status"] = "skipped"
            try:
                await update_opportunity_trader_decision(
                    opportunity_id=opportunity_id,
                    trader_decision=output.decision.action,
                    trader_tldr=output.tldr,
                    status="skipped" if output.decision.action == "REJECT" else None,
                )
            except Exception as e:
                logfire.error("DB write failed for trader decision", opportunity_id=opportunity_id, error=str(e))

            opp_file = find_opportunity_file_by_id(opportunity_id, paper=settings.trading.paper_mode)
            if opp_file:
                try:
                    update_opportunity_frontmatter(opp_file, frontmatter_updates)
                except Exception as e:
                    logfire.error("Failed to persist trader verdict", opportunity_id=opportunity_id, error=str(e))

            # Deterministic Telegram alert — always fires
            await _send_telegram_alert(telegram_client, opportunity, output)

        await _log_trader_decision(opportunity, output)
        return output


async def _execute_trade(
    client: KalshiClient,
    opportunity: OpportunitySignal,
    output: TraderOutput,
    side: str,
    target_price: float,
    settings: Settings,
) -> TraderOutput:
    """Run slippage check, then execute or skip the trade. Returns updated output."""
    contracts = settings.trading.contracts

    with logfire.span("slippage check", ticker=opportunity.market_ticker):
        market = await client.get_market(opportunity.market_ticker)
        if side == "yes":
            current_price_decimal = market.yes_ask / 100
        else:
            current_price_decimal = market.no_ask / 100
        if target_price > 0:
            slippage_pct = abs(current_price_decimal - target_price) / target_price
        else:
            slippage_pct = 0.0
        logfire.info(
            "Slippage check",
            slippage_pct=round(slippage_pct, 4),
            current_price=round(current_price_decimal, 4),
        )

    max_slippage = settings.execution.max_slippage_pct
    if slippage_pct > max_slippage:
        logfire.warn("Slippage too high", slippage_pct=round(slippage_pct, 4), max_slippage=max_slippage)
        return output.model_copy(update={"execution_status": "rejected"})

    if settings.trading.paper_mode:
        logfire.info(
            "Paper mode: skipping execution",
            ticker=opportunity.market_ticker,
            decision=output.decision.action,
            slippage_pct=round(slippage_pct, 4),
        )
        return output.model_copy(update={"execution_status": "paper"})

    initial_price_cents = int(current_price_decimal * 100)

    with logfire.span("order execution", ticker=opportunity.market_ticker, side=side, contracts=contracts):
        order_result = await execute_working_order(
            client=client,
            ticker=opportunity.market_ticker,
            side=side,
            contracts=contracts,
            initial_price_cents=initial_price_cents,
            config=settings,
        )
        logfire.info(
            "Order result",
            status=order_result.status,
            contracts_filled=order_result.contracts_filled,
            fill_price=order_result.fill_price,
        )

    output = output.model_copy(update={
        "order_id": order_result.order_id,
        "fill_price": order_result.fill_price,
        "contracts_filled": order_result.contracts_filled,
        "total_cost_usd": order_result.total_cost_usd,
        "execution_status": order_result.status,
    })

    if order_result.contracts_filled > 0:
        position_id = f"pos_{uuid4().hex[:8]}"

        await _update_state_after_trade(
            opportunity=opportunity,
            side=side.upper(),
            contracts=order_result.contracts_filled,
            fill_price=order_result.fill_price or current_price_decimal,
            total_cost=order_result.total_cost_usd,
            config=settings,
            position_id=position_id,
        )

        trade = TradeExecution(
            id=generate_trade_id(),
            position_id=position_id,
            opportunity_id=opportunity.id,
            market_ticker=opportunity.market_ticker,
            side=side.upper(),
            action="BUY",
            contracts=order_result.contracts_filled,
            price=order_result.fill_price or current_price_decimal,
            total=order_result.total_cost_usd,
            paper=False,
            executed_at=datetime.now(timezone.utc),
        )
        try:
            await save_trade_to_db(trade)
        except Exception as e:
            logfire.error("DB write failed for trade", trade_id=trade.id, error=str(e))

        log_trade(trade)

        if order_result.fill_price:
            fill_price_rounded = round(order_result.fill_price, 4)
        else:
            fill_price_rounded = None

        if order_result.total_cost_usd:
            total_cost_rounded = round(order_result.total_cost_usd, 2)
        else:
            total_cost_rounded = None

        logfire.info(
            "Trade executed",
            ticker=opportunity.market_ticker,
            side=side,
            contracts=order_result.contracts_filled,
            fill_price=fill_price_rounded,
            total_cost_usd=total_cost_rounded,
        )

    return output


_DECISION_LABELS = {
    "REJECT": "REJECTED",
    "EXECUTE_BUY_YES": "EXECUTED \u00B7 BUY YES",
    "EXECUTE_BUY_NO": "EXECUTED \u00B7 BUY NO",
}


async def _send_telegram_alert(
    telegram_client: TelegramClient | None,
    opportunity: OpportunitySignal,
    output: TraderOutput,
) -> None:
    """Send a deterministic Telegram alert for every trader decision."""
    if telegram_client is None:
        return

    decision_label = _DECISION_LABELS.get(output.decision.action, output.decision.action)

    message = (
        f"TRADE DECISION\n\n"
        f"{opportunity.market_ticker}\n"
        f"{decision_label}\n\n"
        f"{output.tldr}"
    )
    try:
        await telegram_client.send_alert(message)
    except Exception as e:
        logger.warning("Telegram alert failed (non-fatal): %s", e)


async def _log_trader_decision(
    opportunity: OpportunitySignal,
    output: TraderOutput,
) -> None:
    """Log a trading decision to the persistent decision log."""
    try:
        entry = DecisionEntry(
            opportunity_id=opportunity.id,
            ticker=opportunity.market_ticker,
            action=output.decision.action,
            price=output.fill_price or opportunity.yes_price,
            contracts=output.contracts_filled,
            confidence=output.decision.confidence,
            reasoning=output.decision.reasoning,
            tldr=output.tldr,
            execution_status=output.execution_status,
        )
        try:
            await save_decision_to_db(entry)
        except Exception as e:
            logfire.error("DB write failed for decision", opportunity_id=opportunity.id, error=str(e))

        log_decision(entry)
    except Exception as e:
        logger.error("Failed to log decision for %s: %s", opportunity.market_ticker, e)


async def _update_state_after_trade(
    opportunity: OpportunitySignal,
    side: Literal["YES", "NO"],
    contracts: int,
    fill_price: float,
    total_cost: float,
    config: Settings,
    position_id: str,
) -> None:
    """Update state.yaml with new position and adjust portfolio balances."""
    state = await load_state_from_db()

    new_cash = state.portfolio.cash_balance - total_cost
    new_positions_value = state.portfolio.positions_value + total_cost
    new_portfolio = PortfolioStats(
        cash_balance=new_cash,
        positions_value=new_positions_value,
        total_value=new_cash + new_positions_value,
    )
    position = Position(
        id=position_id,
        market_ticker=opportunity.market_ticker,
        side=side,
        contracts=contracts,
        average_entry=fill_price,
        current_price=fill_price,
        opportunity_id=opportunity.id,
    )
    new_state = PortfolioState(
        last_updated=state.last_updated,
        portfolio=new_portfolio,
        open_positions=[*state.open_positions, position],
        closed_positions=state.closed_positions,
        seen_tickers=state.seen_tickers,
    )
    try:
        await update_portfolio_after_trade_in_db(
            position=position,
            cash_balance=new_cash,
            positions_value=new_positions_value,
            total_value=new_cash + new_positions_value,
        )
    except Exception as e:
        logfire.error("DB write failed for portfolio update", opportunity_id=opportunity.id, error=str(e))

    save_state(new_state)
    logger.info(
        "Updated state: cash=$%.2f, positions=%d",
        new_cash,
        len(new_state.open_positions),
    )
