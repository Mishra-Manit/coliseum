"""Trader Agent: Final decision-maker and trade executor."""

import asyncio
import logging
from contextlib import AsyncExitStack
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

import logfire

from pydantic_ai import Agent, RunContext

from coliseum.agents.agent_factory import AgentFactory
from coliseum.agents.trader.models import (
    OrderResult,
    TraderDependencies,
    TraderOutput,
)
from coliseum.agents.trader.prompts import (
    build_trader_system_prompt,
    _build_trader_prompt,
)
from coliseum.config import Settings, get_settings
from coliseum.llm_providers import OpenAIModel, get_model_string
from coliseum.services.kalshi.client import KalshiClient
from coliseum.services.kalshi.config import KalshiConfig
from coliseum.services.telegram import create_telegram_client
from coliseum.storage.files import (
    TradeExecution,
    get_opportunity_markdown_body,
    find_opportunity_file_by_id,
    generate_trade_id,
    load_opportunity_from_file,
    log_trade,
    update_opportunity_frontmatter,
)
from coliseum.memory.decisions import DecisionEntry, log_decision
from coliseum.storage.state import (
    Position,
    load_state,
    save_state,
)

logger = logging.getLogger(__name__)


def _create_agent(settings: Settings) -> Agent[TraderDependencies, TraderOutput]:
    """Create the Trader agent."""
    return Agent(
        model=get_model_string(OpenAIModel.GPT_5_2),
        output_type=TraderOutput,
        deps_type=TraderDependencies,
        system_prompt=build_trader_system_prompt(settings),
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
        return {
            "ticker": ticker,
            "yes_ask": market.yes_ask,
            "yes_price_decimal": market.yes_ask / 100 if market.yes_ask else None,
            "no_ask": market.no_ask,
            "no_price_decimal": market.no_ask / 100 if market.no_ask else None,
        }

    _register_telegram_tool(agent)


def _register_telegram_tool(agent: Agent[TraderDependencies, TraderOutput]) -> None:
    """Register the Telegram alert tool."""
    @agent.tool
    async def send_telegram_alert(
        ctx: RunContext[TraderDependencies],
        event_title: str,
        event_subtitle: str | None,
        decision: str,
        reason: str,
    ) -> dict:
        """Send a Telegram alert about the trading decision."""
        try:
            if not ctx.deps.config.telegram.send_alerts:
                return {
                    "success": True,
                    "skipped": True,
                    "reason": "Telegram alerts are disabled in config",
                }

            if ctx.deps.telegram_client is None:
                return {
                    "success": False,
                    "error": "Telegram client not configured",
                }

            subtitle_part = f"\n{event_subtitle}" if event_subtitle else ""
            message = f"🎯 {event_title}{subtitle_part}\n\n{decision}: {reason}"

            result = await ctx.deps.telegram_client.send_alert(message)

            if result.success:
                return {
                    "success": True,
                    "message_id": result.message_id,
                    "recipient": result.recipient,
                }
            else:
                return {
                    "success": False,
                    "error": result.error or "Unknown error",
                }

        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")
            return {
                "success": False,
                "error": str(e),
            }


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
                logger.info(
                    f"Placed order {order_id}: {contracts} {side} @ {current_price}¢"
                )
            else:
                # Reprice existing order
                order = await client.amend_order(order_id, price=current_price)
                logger.info(f"Repriced order {order_id} to {current_price}¢ (attempt {attempt})")

            # Wait for fill
            await asyncio.sleep(check_interval)

            # Check status
            order = await client.get_order_status(order_id)

            if order.is_filled:
                # Fully filled — fall back to `contracts` if Kalshi omits fill counts
                actual_fill_count = order.fill_count if order.fill_count > 0 else contracts
                if order.fill_count > 0:
                    fill_price_decimal = (
                        (order.taker_fill_cost + order.maker_fill_cost)
                        / (order.fill_count * 100)
                    )
                    total_cost = (order.taker_fill_cost + order.maker_fill_cost) / 100
                else:
                    fill_price_decimal = current_price / 100
                    total_cost = actual_fill_count * fill_price_decimal

                return OrderResult(
                    order_id=order_id,
                    fill_price=fill_price_decimal,
                    contracts_filled=actual_fill_count,
                    total_cost_usd=total_cost,
                    status="filled",
                )

            # Check if partial fill is worth keeping
            fill_pct = order.fill_count / contracts if contracts > 0 else 0.0
            if fill_pct >= config.execution.min_fill_pct_to_keep:
                # Keep partial fill
                fill_price_decimal = (
                    (order.taker_fill_cost + order.maker_fill_cost)
                    / (order.fill_count * 100)
                    if order.fill_count > 0
                    else current_price / 100
                )
                total_cost = (order.taker_fill_cost + order.maker_fill_cost) / 100

                await client.cancel_order(order_id)
                logger.info(f"Keeping partial fill: {order.fill_count}/{contracts}")

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
                logger.info(f"Repricing to {current_price}¢ for next attempt")
            else:
                # Out of attempts, cancel
                await client.cancel_order(order_id)
                logger.info(f"Cancelled order {order_id} after {max_attempts} attempts")

                # Final poll — catch any fills that landed during the cancel window
                refreshed = None
                try:
                    refreshed = await client.get_order_status(order_id)
                except Exception as exc:
                    logger.warning(f"Final status poll failed for {order_id}: {exc}")

                order = refreshed if refreshed is not None else order

                # Return partial fill if any
                if order.fill_count > 0:
                    fill_price_decimal = (
                        (order.taker_fill_cost + order.maker_fill_cost)
                        / (order.fill_count * 100)
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
            logger.error(f"Error in working order execution: {e}")
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

    # Load opportunity file
    opp_file = find_opportunity_file_by_id(opportunity_id, paper=settings.trading.paper_mode)
    if not opp_file:
        raise FileNotFoundError(f"Opportunity file not found: {opportunity_id}")

    opportunity = load_opportunity_from_file(opp_file)

    if not opportunity.recommendation_completed_at:
        raise ValueError(f"Recommendation not completed for {opportunity_id}")

    kalshi_config = KalshiConfig()
    # No auth needed in paper mode — market reads work unauthenticated; execution is skipped
    private_key_pem = "" if settings.trading.paper_mode else settings.get_rsa_private_key()

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
            if settings.telegram.send_alerts:
                telegram_client = await stack.enter_async_context(
                    create_telegram_client(
                        bot_token=settings.telegram_bot_token,
                        chat_id=settings.telegram_chat_id,
                    )
                )

            deps = TraderDependencies(
                kalshi_client=client,
                telegram_client=telegram_client,
                opportunity_id=opportunity_id,
                config=settings,
            )

            markdown_body = get_opportunity_markdown_body(opp_file)
            prompt = _build_trader_prompt(opportunity, markdown_body, settings)

            with logfire.span("agent decision", ticker=opportunity.market_ticker):
                agent = get_agent(settings)
                result = await agent.run(prompt, deps=deps)
                output: TraderOutput = result.output
                logfire.info("Decision made", action=output.decision.action)

            if output.decision.action == "REJECT":
                output.execution_status = "skipped"
                try:
                    update_opportunity_frontmatter(opp_file, {"status": "skipped"})
                except Exception as e:
                    logfire.error("Failed to persist skipped status", opportunity_id=opportunity_id, error=str(e))
                _log_trader_decision(opportunity, output)
                logfire.info("Trade rejected", reasoning=output.decision.reasoning)
                return output

            if output.decision.action == "EXECUTE_BUY_YES":
                side = "yes"
                target_price = opportunity.yes_price
            else:
                side = "no"
                target_price = opportunity.no_price

            contracts = settings.trading.contracts

            with logfire.span("slippage check", ticker=opportunity.market_ticker):
                market = await client.get_market(opportunity.market_ticker)
                current_price_decimal = (
                    market.yes_ask / 100 if side == "yes" else market.no_ask / 100
                )
                slippage_pct = abs(current_price_decimal - target_price) / target_price if target_price > 0 else 0.0
                logfire.info(
                    "Slippage check",
                    slippage_pct=round(slippage_pct, 4),
                    current_price=round(current_price_decimal, 4),
                )

            max_slippage = settings.execution.max_slippage_pct
            if slippage_pct > max_slippage:
                logfire.warn("Slippage too high", slippage_pct=round(slippage_pct, 4), max_slippage=max_slippage)
                output.execution_status = "rejected"
                return output

            if settings.trading.paper_mode:
                logfire.info(
                    "Paper mode: skipping execution",
                    ticker=opportunity.market_ticker,
                    decision=output.decision.action,
                    slippage_pct=round(slippage_pct, 4),
                )
                output.execution_status = "paper"
                return output

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

            output.order_id = order_result.order_id
            output.fill_price = order_result.fill_price
            output.contracts_filled = order_result.contracts_filled
            output.total_cost_usd = order_result.total_cost_usd
            output.execution_status = order_result.status

            if order_result.contracts_filled > 0:
                _update_state_after_trade(
                    opportunity=opportunity,
                    side=side.upper(),
                    contracts=order_result.contracts_filled,
                    fill_price=order_result.fill_price or current_price_decimal,
                    total_cost=order_result.total_cost_usd,
                    config=settings,
                    reasoning=output.decision.reasoning,
                )

                trade = TradeExecution(
                    id=generate_trade_id(),
                    position_id=f"pos_{uuid4().hex[:8]}",
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
                log_trade(trade)

                logfire.info(
                    "Trade executed",
                    ticker=opportunity.market_ticker,
                    side=side,
                    contracts=order_result.contracts_filled,
                    fill_price=round(order_result.fill_price, 4) if order_result.fill_price else None,
                    total_cost_usd=round(order_result.total_cost_usd, 2) if order_result.total_cost_usd else None,
                )

        _log_trader_decision(opportunity, output)
        return output


def _log_trader_decision(
    opportunity,
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
            execution_status=output.execution_status,
        )
        log_decision(entry)
    except Exception as e:
        logger.error("Failed to log decision for %s: %s", opportunity.market_ticker, e)


def _update_state_after_trade(
    opportunity,
    side: Literal["YES", "NO"],
    contracts: int,
    fill_price: float,
    total_cost: float,
    config: Settings,
    reasoning: str | None = None,
) -> None:
    """Update state.yaml with new position and adjust portfolio balances."""
    state = load_state()

    state.portfolio.cash_balance -= total_cost
    state.portfolio.positions_value += total_cost
    state.portfolio.total_value = state.portfolio.cash_balance + state.portfolio.positions_value

    position = Position(
        id=f"pos_{uuid4().hex[:8]}",
        market_ticker=opportunity.market_ticker,
        side=side,
        contracts=contracts,
        average_entry=fill_price,
        current_price=fill_price,
        opportunity_id=opportunity.id,
    )
    state.open_positions.append(position)

    save_state(state)
    logger.info(f"Updated state: cash=${state.portfolio.cash_balance:.2f}, positions={len(state.open_positions)}")
