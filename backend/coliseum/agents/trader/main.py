"""Trader Agent: Final decision-maker and trade executor."""

import asyncio
import json
import logging
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage

from coliseum.agents.agent_factory import AgentFactory
from coliseum.agents.shared_tools import register_load_opportunity_with_research
from coliseum.agents.trader.models import (
    OrderResult,
    TraderDependencies,
    TraderOutput,
)
from coliseum.agents.trader.prompts import (
    build_trader_system_prompt,
    build_trader_sure_thing_system_prompt,
    _build_trader_prompt,
    _build_trader_sure_thing_prompt,
)
from coliseum.config import Settings, get_settings
from coliseum.llm_providers import OpenAIModel, get_model_string
from coliseum.services.kalshi.client import KalshiClient
from coliseum.services.telegram import create_telegram_client
from coliseum.storage.files import (
    TradeExecution,
    get_opportunity_markdown_body,
    find_opportunity_file_by_id,
    generate_trade_id,
    load_opportunity_from_file,
    log_trade,
    update_opportunity_status,
)
from coliseum.storage.memory import TradeDetails, update_entry
from coliseum.storage.state import (
    Position,
    load_state,
    save_state,
)

logger = logging.getLogger(__name__)


async def simulate_limit_order(
    ticker: str,
    side: Literal["yes", "no"],
    contracts: int,
    price_cents: int,
) -> dict:
    """Simulate a limit order by logging intent to console."""
    message = (
        f"[SIMULATED TRADE] {contracts} {side.upper()} contracts "
        f"for {ticker} @ {price_cents}¢"
    )
    print(message)
    logger.info(message)

    return {
        "order_id": f"sim_{uuid4().hex[:8]}",
        "status": "simulated",
        "remaining_count": contracts,
        "fill_count": 0,
    }


def _create_edge_agent(settings: Settings) -> Agent[TraderDependencies, TraderOutput]:
    """Create the Trader agent for edge trading strategy."""
    return Agent(
        model=get_model_string(OpenAIModel.GPT_5_2),
        output_type=TraderOutput,
        deps_type=TraderDependencies,
        system_prompt=build_trader_system_prompt(settings),
    )


def _create_sure_thing_agent(settings: Settings) -> Agent[TraderDependencies, TraderOutput]:
    """Create the Trader agent for sure thing strategy (simplified)."""
    return Agent(
        model=get_model_string(FireworksModel.KIMI_K_2_5),
        output_type=TraderOutput,
        deps_type=TraderDependencies,
        system_prompt=build_trader_sure_thing_system_prompt(settings),
    )


def _register_edge_tools(agent: Agent[TraderDependencies, TraderOutput]) -> None:
    """Register tools with the Trader agent for edge trading."""
    register_load_opportunity_with_research(agent, include_metrics=True)

    @agent.tool
    async def check_portfolio_state(
        ctx: RunContext[TraderDependencies],
    ) -> dict:
        """Get portfolio cash, positions for trade validation."""
        state = load_state()
        return {
            "cash_balance": state.portfolio.cash_balance,
            "total_value": state.portfolio.total_value,
            "positions_value": state.portfolio.positions_value,
            "open_positions_count": len(state.open_positions),
        }

    @agent.tool
    async def get_current_market_price(
        ctx: RunContext[TraderDependencies],
        ticker: str,
    ) -> dict:
        """Fetch live Kalshi orderbook prices (bid/ask for yes/no in cents)."""
        client = ctx.deps.kalshi_client
        market = await client.get_market(ticker)
        return {
            "ticker": ticker,
            "yes_bid": market.yes_bid,
            "yes_ask": market.yes_ask,
            "no_bid": market.no_bid,
            "no_ask": market.no_ask,
            "yes_price_decimal": market.yes_ask / 100 if market.yes_ask else None,
            "no_price_decimal": market.no_ask / 100 if market.no_ask else None,
        }

    @agent.tool
    async def calculate_slippage(
        ctx: RunContext[TraderDependencies],
        recommendation_price: float,
        current_price: float,
    ) -> dict:
        """Compute price movement since recommendation was generated (both prices 0.0-1.0)."""
        slippage = abs(current_price - recommendation_price)
        slippage_pct = slippage / recommendation_price if recommendation_price > 0 else 0.0
        return {
            "slippage_absolute": slippage,
            "slippage_pct": slippage_pct,
            "price_moved_up": current_price > recommendation_price,
        }

    @agent.tool
    async def place_limit_order(
        ctx: RunContext[TraderDependencies],
        ticker: str,
        side: Literal["yes", "no"],
        contracts: int,
        price_cents: int,
    ) -> dict:
        """Simulate limit order without calling Kalshi (logs to console, returns fake order_id)."""
        return await simulate_limit_order(
            ticker=ticker,
            side=side,
            contracts=contracts,
            price_cents=price_cents,
        )

    @agent.tool
    async def get_order_status(
        ctx: RunContext[TraderDependencies],
        order_id: str,
    ) -> dict:
        """Poll order status from Kalshi (filled/partial/pending with fill counts)."""
        client = ctx.deps.kalshi_client
        order = await client.get_order_status(order_id)
        return {
            "order_id": order.order_id,
            "status": order.status,
            "fill_count": order.fill_count,
            "remaining_count": order.remaining_count,
            "is_filled": order.is_filled,
            "is_partial": order.is_partial,
            "taker_fill_count": order.taker_fill_count,
            "maker_fill_count": order.maker_fill_count,
            "taker_fill_cost": order.taker_fill_cost,
            "maker_fill_cost": order.maker_fill_cost,
        }

    @agent.tool
    async def cancel_order(
        ctx: RunContext[TraderDependencies],
        order_id: str,
    ) -> dict:
        """Cancel unfilled or partially filled order on Kalshi."""
        client = ctx.deps.kalshi_client
        order = await client.cancel_order(order_id)
        return {
            "order_id": order.order_id,
            "status": order.status,
            "fill_count": order.fill_count,
        }

    @agent.tool
    async def amend_order(
        ctx: RunContext[TraderDependencies],
        order_id: str,
        new_price_cents: int,
    ) -> dict:
        """Reprice existing order to increase aggression (walk up the orderbook)."""
        client = ctx.deps.kalshi_client
        order = await client.amend_order(order_id, price=new_price_cents)
        return {
            "order_id": order.order_id,
            "status": order.status,
            "remaining_count": order.remaining_count,
            "fill_count": order.fill_count,
        }

    _register_telegram_tool(agent)


def _register_sure_thing_tools(agent: Agent[TraderDependencies, TraderOutput]) -> None:
    """Register minimal tools for sure thing trading (no portfolio/slippage calculations)."""
    register_load_opportunity_with_research(agent, include_metrics=False)

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
    """Register the Telegram alert tool (shared between strategies)."""
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
                # Fully filled
                fill_price_decimal = (
                    (order.taker_fill_cost + order.maker_fill_cost)
                    / (order.fill_count * 100)
                    if order.fill_count > 0
                    else current_price / 100
                )
                total_cost = (order.taker_fill_cost + order.maker_fill_cost) / 100

                return OrderResult(
                    order_id=order_id,
                    fill_price=fill_price_decimal,
                    contracts_filled=order.fill_count,
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


_edge_factory: AgentFactory[TraderDependencies, TraderOutput] | None = None
_sure_thing_factory: AgentFactory[TraderDependencies, TraderOutput] | None = None


def get_agent(settings: Settings, strategy: str = "edge") -> Agent[TraderDependencies, TraderOutput]:
    """Get the singleton Trader agent instance for the given strategy."""
    global _edge_factory, _sure_thing_factory

    if strategy == "sure_thing":
        if _sure_thing_factory is None:
            _sure_thing_factory = AgentFactory(
                create_fn=lambda: _create_sure_thing_agent(settings),
                register_tools_fn=_register_sure_thing_tools,
            )
        return _sure_thing_factory.get_agent()

    if _edge_factory is None:
        _edge_factory = AgentFactory(
            create_fn=lambda: _create_edge_agent(settings),
            register_tools_fn=_register_edge_tools,
        )
    return _edge_factory.get_agent()


async def run_trader(
    opportunity_id: str,
    settings: Settings | None = None,
) -> TraderOutput:
    """Execute or reject trade after validating recommendation, checking slippage, and verifying risk limits."""
    if settings is None:
        settings = get_settings()

    logger.info(f"Starting Trader for opportunity: {opportunity_id}")

    # Load opportunity file
    opp_file = find_opportunity_file_by_id(opportunity_id)
    if not opp_file:
        raise FileNotFoundError(f"Opportunity file not found: {opportunity_id}")

    opportunity = load_opportunity_from_file(opp_file)

    # Verify recommendation exists
    if not opportunity.recommendation_completed_at:
        raise ValueError(f"Recommendation not completed for {opportunity_id}")

    if opportunity.strategy != "sure_thing":
        if opportunity.edge is None or opportunity.expected_value is None:
            raise ValueError(f"Missing edge/EV data for {opportunity_id}")

    # Create Kalshi client
    from coliseum.services.kalshi.config import KalshiConfig

    kalshi_config = KalshiConfig(paper_mode=settings.trading.paper_mode)
    private_key_pem = "" if settings.trading.paper_mode else settings.get_rsa_private_key()
    async with KalshiClient(
        config=kalshi_config,
        api_key=settings.kalshi_api_key,
        private_key_pem=private_key_pem,
    ) as client, create_telegram_client(
        bot_token=settings.telegram_bot_token,
        chat_id=settings.telegram_chat_id,
    ) as telegram_client:
        deps = TraderDependencies(
            kalshi_client=client,
            telegram_client=telegram_client,
            opportunity_id=opportunity_id,
            config=settings,
        )

        # Build prompt based on strategy
        markdown_body = get_opportunity_markdown_body(opp_file)
        strategy = opportunity.strategy
        if strategy == "sure_thing":
            prompt = _build_trader_sure_thing_prompt(opportunity, markdown_body, settings)
        else:
            prompt = _build_trader_prompt(opportunity, markdown_body, settings)

        # Run agent
        agent = get_agent(settings, strategy)
        result = await agent.run(prompt, deps=deps)
        output: TraderOutput = result.output

        # Handle execution based on decision
        if output.decision.action == "REJECT":
            logger.info(f"Trader REJECTED trade: {output.decision.reasoning}")
            update_opportunity_status(opportunity.market_ticker, "skipped")
            update_entry(
                market_ticker=opportunity.market_ticker,
                status="SKIPPED",
            )
            return output

        # Determine side and get corresponding metrics
        if output.decision.action == "EXECUTE_BUY_YES":
            side = "yes"
            target_price = opportunity.yes_price
        else:  # EXECUTE_BUY_NO
            side = "no"
            target_price = opportunity.no_price
        
        if opportunity.strategy == "sure_thing":
            edge = 0.0
            ev = 0.0
            position_pct = 0.0
        elif side == "yes":
            edge = opportunity.edge
            ev = opportunity.expected_value
            position_pct = opportunity.suggested_position_pct or 0.0
        else:
            edge = opportunity.edge_no
            ev = opportunity.expected_value_no
            position_pct = opportunity.suggested_position_pct_no or 0.0

        # Calculate position size
        if opportunity.strategy == "sure_thing":
            contracts = 3
        else:
            portfolio_state = load_state()
            trade_size_usd = portfolio_state.portfolio.total_value * position_pct
            contracts = int(trade_size_usd / target_price) if target_price > 0 else 0

        # Get current market price and calculate slippage
        market = await client.get_market(opportunity.market_ticker)
        current_price_decimal = (
            market.yes_ask / 100 if side == "yes" else market.no_ask / 100
        )
        slippage_pct = abs(current_price_decimal - target_price) / target_price if target_price > 0 else 0.0

        # Final risk check - verify slippage is acceptable
        max_slippage = settings.execution.max_slippage_pct
        if slippage_pct > max_slippage:
            logger.warning(f"Slippage too high: {slippage_pct:.1%} > {max_slippage:.0%}")
            output.execution_status = "rejected"
            update_opportunity_status(opportunity.market_ticker, "skipped")
            update_entry(
                market_ticker=opportunity.market_ticker,
                status="SKIPPED",
            )
            return output

        initial_price_cents = int(current_price_decimal * 100)
        order_result = await execute_working_order(
            client=client,
            ticker=opportunity.market_ticker,
            side=side,
            contracts=contracts,
            initial_price_cents=initial_price_cents,
            config=settings,
        )

        # Update output with execution results
        output.order_id = order_result.order_id
        output.fill_price = order_result.fill_price
        output.contracts_filled = order_result.contracts_filled
        output.total_cost_usd = order_result.total_cost_usd
        output.execution_status = order_result.status

        # Update state and log trade if filled
        if order_result.contracts_filled > 0:
            _update_state_after_trade(
                opportunity=opportunity,
                side=side.upper(),
                contracts=order_result.contracts_filled,
                fill_price=order_result.fill_price or current_price_decimal,
                total_cost=order_result.total_cost_usd,
                config=settings,
            )

            # Log trade (use metrics for chosen side)
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
                portfolio_pct=position_pct,
                edge=edge,
                ev=ev,
                paper=settings.trading.paper_mode,
                executed_at=datetime.now(timezone.utc),
            )
            log_trade(trade)

            # Update opportunity status
            update_opportunity_status(opportunity.market_ticker, "traded")

            update_entry(
                market_ticker=opportunity.market_ticker,
                status="EXECUTED",
                trade=TradeDetails(
                    side=side.upper(),  # type: ignore
                    contracts=order_result.contracts_filled,
                    entry_price=order_result.fill_price or current_price_decimal,
                    reasoning=output.decision.reasoning,
                ),
            )

            logger.info(
                f"Trade executed: {order_result.contracts_filled} {side} contracts @ "
                f"{order_result.fill_price:.2%} (${order_result.total_cost_usd:.2f})"
            )

        return output


def _update_state_after_trade(
    opportunity,
    side: Literal["YES", "NO"],
    contracts: int,
    fill_price: float,
    total_cost: float,
    config: Settings,
) -> None:
    """Update state.yaml with new position, adjust cash balance, and recalculate risk metrics."""
    state = load_state()

    # Update cash balance
    state.portfolio.cash_balance -= total_cost
    state.portfolio.positions_value += total_cost
    state.portfolio.total_value = (
        state.portfolio.cash_balance + state.portfolio.positions_value
    )

    # Create position
    position_id = f"pos_{uuid4().hex[:8]}"
    position = Position(
        id=position_id,
        market_ticker=opportunity.market_ticker,
        side=side,
        contracts=contracts,
        average_entry=fill_price,
        current_price=fill_price,  # Will be updated by Guardian
        unrealized_pnl=0.0,  # Will be calculated by Guardian
    )
    state.open_positions.append(position)

    save_state(state)
    logger.info(f"Updated state: cash=${state.portfolio.cash_balance:.2f}, positions={len(state.open_positions)}")
