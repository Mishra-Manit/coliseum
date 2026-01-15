"""
Agent Runner

Parallel execution of 8 AI agent betting decisions.

Runs all 8 agents in parallel per event with individual timeouts.
Handles timeouts (5 min per agent) with auto-ABSTAIN fallback.
Each agent gets intelligence brief + personal context (bankroll, history, persona).
"""

import asyncio
import logfire
from typing import Any

from pipeline.utils import create_agent
from models.pipeline.decisions import BetDecision


# System prompt template for betting agents
BETTING_SYSTEM_PROMPT = """You are {agent_name}, an AI prediction market trader.

Persona: {persona_description}

Your goal is to maximize your bankroll over time by making accurate predictions.
You should carefully analyze the intelligence brief and your historical performance.

Decision Guidelines:
- decision: "YES" (buy YES shares), "NO" (buy NO shares), or "ABSTAIN" (skip this market)
- amount: Dollar amount to bet (cannot exceed 10% of your current bankroll)
- confidence: Your confidence level from 0 (no confidence) to 1 (certain)
- reasoning: Provide detailed step-by-step reasoning for your decision

Risk Management:
- Never bet more than 10% of your bankroll on a single event
- Consider your recent performance and adjust bet sizing accordingly
- ABSTAIN if the market is unclear or insufficient information is available
- Factor in the current price when deciding which side to bet on

You must output a structured decision in the exact format specified."""


# Configuration for 8 AI betting agents
AGENT_CONFIGS = [
    {
        "id": "gpt-4o",
        "name": "GPT-4o",
        "model": "openrouter:openai/gpt-4o",
        "persona_id": "analytical_trader",
    },
    {
        "id": "claude-3.5",
        "name": "Claude 3.5 Sonnet",
        "model": "openrouter:anthropic/claude-3.5-sonnet",
        "persona_id": "contrarian_investor",
    },
    {
        "id": "grok-2",
        "name": "Grok-2",
        "model": "openrouter:x-ai/grok-2",
        "persona_id": "momentum_trader",
    },
    {
        "id": "gemini-pro",
        "name": "Gemini Pro",
        "model": "openrouter:google/gemini-pro-1.5",
        "persona_id": "value_investor",
    },
    {
        "id": "llama-3.1",
        "name": "Llama 3.1",
        "model": "openrouter:meta-llama/llama-3.1-405b",
        "persona_id": "risk_manager",
    },
    {
        "id": "mistral-large",
        "name": "Mistral Large",
        "model": "openrouter:mistralai/mistral-large",
        "persona_id": "quantitative_analyst",
    },
    {
        "id": "deepseek-v2",
        "name": "DeepSeek V2",
        "model": "openrouter:deepseek/deepseek-chat",
        "persona_id": "technical_analyst",
    },
    {
        "id": "qwen-max",
        "name": "Qwen Max",
        "model": "openrouter:qwen/qwen-max",
        "persona_id": "fundamental_analyst",
    },
]


# Default persona descriptions (can be overridden by loading from YAML)
DEFAULT_PERSONAS = {
    "analytical_trader": "You are a systematic, data-driven trader who relies on statistical analysis and historical patterns.",
    "contrarian_investor": "You look for opportunities where the market consensus may be wrong, betting against the crowd when justified.",
    "momentum_trader": "You follow trends and market momentum, betting on events that show strong directional movement.",
    "value_investor": "You seek undervalued opportunities where the market price doesn't reflect true probability.",
    "risk_manager": "You prioritize capital preservation, taking only high-confidence bets with favorable risk-reward ratios.",
    "quantitative_analyst": "You use quantitative models and data analysis to identify probability edges in the market.",
    "technical_analyst": "You analyze patterns, trends, and market psychology to make betting decisions.",
    "fundamental_analyst": "You focus on fundamental factors and real-world events to assess probabilities.",
}


class BettingAgentRunner:
    """Manages and runs 8 AI betting agents in parallel."""

    def __init__(self):
        """Initialize 8 AI betting agents with configured models and personas."""
        self.agents = {}
        self.agent_configs = AGENT_CONFIGS

        for config in self.agent_configs:
            persona = self._load_persona(config['persona_id'])

            system_prompt = BETTING_SYSTEM_PROMPT.format(
                agent_name=config['name'],
                persona_description=persona
            )

            logfire.info(
                "Creating betting agent",
                agent_id=config['id'],
                agent_name=config['name'],
                model=config['model']
            )

            self.agents[config['id']] = create_agent(
                model=config['model'],
                output_type=BetDecision,
                system_prompt=system_prompt,
                temperature=0.3,  # Slightly creative for diverse strategies
                retries=2,
                timeout=120.0  # 2 minutes per agent
            )

        logfire.info(f"Initialized {len(self.agents)} betting agents")

    async def run_all_agents_for_event(
        self,
        event: dict[str, Any],
        intelligence_brief: str
    ) -> list[BetDecision]:
        """Run all 8 agents in parallel for one event.

        Args:
            event: Event dictionary with keys:
                - ticker: Kalshi market ticker
                - question: Market question
                - yes_price: Current YES price
                - close_time: Market close time
            intelligence_brief: Formatted intelligence brief text

        Returns:
            List of 8 BetDecision objects (some may be ABSTAIN)
        """
        with logfire.span("betting.run_all_agents", event_id=event.get('ticker')):
            logfire.info(
                "Running all agents for event",
                event_ticker=event.get('ticker'),
                agent_count=len(self.agents)
            )

            # Create tasks for parallel execution
            tasks = []
            for agent_id in self.agents.keys():
                task = asyncio.create_task(
                    self._run_single_agent_with_timeout(
                        agent_id,
                        event,
                        intelligence_brief
                    )
                )
                tasks.append((agent_id, task))

            # Wait for all agents (with individual timeouts)
            decisions = []
            for agent_id, task in tasks:
                try:
                    decision = await task
                    decisions.append(decision)

                    logfire.info(
                        "Agent decision received",
                        agent_id=agent_id,
                        decision=decision.decision,
                        amount=decision.amount,
                        confidence=decision.confidence
                    )

                except Exception as e:
                    # This should not happen as timeout is handled in _run_single_agent_with_timeout
                    logfire.error(
                        "Unexpected error from agent",
                        agent_id=agent_id,
                        error=str(e)
                    )
                    # Create ABSTAIN decision as fallback
                    decisions.append(BetDecision(
                        agent_id=agent_id,
                        event_id=event.get('ticker', 'UNKNOWN'),
                        decision="ABSTAIN",
                        amount=0.0,
                        confidence=0.0,
                        reasoning=f"Error: {str(e)}"
                    ))

            logfire.info(
                "All agents completed",
                event_ticker=event.get('ticker'),
                total_decisions=len(decisions),
                yes_count=sum(1 for d in decisions if d.decision == "YES"),
                no_count=sum(1 for d in decisions if d.decision == "NO"),
                abstain_count=sum(1 for d in decisions if d.decision == "ABSTAIN")
            )

            return decisions

    async def _run_single_agent_with_timeout(
        self,
        agent_id: str,
        event: dict[str, Any],
        intelligence_brief: str
    ) -> BetDecision:
        """Run a single agent with timeout and auto-ABSTAIN fallback.

        Args:
            agent_id: Agent identifier
            event: Event dictionary
            intelligence_brief: Intelligence brief text

        Returns:
            BetDecision (ABSTAIN on timeout)
        """
        try:
            decision = await asyncio.wait_for(
                self._run_single_agent(agent_id, event, intelligence_brief),
                timeout=300.0  # 5 minutes total timeout
            )
            return decision

        except asyncio.TimeoutError:
            logfire.warn(
                "Agent timed out, defaulting to ABSTAIN",
                agent_id=agent_id,
                event_ticker=event.get('ticker')
            )
            return BetDecision(
                agent_id=agent_id,
                event_id=event.get('ticker', 'UNKNOWN'),
                decision="ABSTAIN",
                amount=0.0,
                confidence=0.0,
                reasoning="Timeout - defaulted to ABSTAIN after 5 minutes"
            )

    async def _run_single_agent(
        self,
        agent_id: str,
        event: dict[str, Any],
        intelligence_brief: str
    ) -> BetDecision:
        """Execute betting decision for one agent.

        Args:
            agent_id: Agent identifier
            event: Event dictionary
            intelligence_brief: Intelligence brief text

        Returns:
            BetDecision from the agent

        Raises:
            AgentExecutionError: If agent execution fails
        """
        with logfire.span("betting.agent_decision", agent_id=agent_id):
            # Load agent context (bankroll, history, etc.)
            agent_context = self._load_agent_context(agent_id)

            # Build prompt with brief + context
            prompt = self._build_betting_prompt(
                event,
                intelligence_brief,
                agent_context
            )

            # Run agent
            agent = self.agents[agent_id]
            result = await agent.run(prompt)
            decision = result.data

            # Validate bet amount doesn't exceed 10% of bankroll
            max_bet = agent_context['bankroll'] * 0.1
            if decision.amount > max_bet:
                logfire.warn(
                    "Agent exceeded max bet size, capping at 10% of bankroll",
                    agent_id=agent_id,
                    requested_amount=decision.amount,
                    max_allowed=max_bet
                )
                decision.amount = max_bet

            return decision

    def _build_betting_prompt(
        self,
        event: dict[str, Any],
        intelligence_brief: str,
        agent_context: dict[str, Any]
    ) -> str:
        """Build the prompt for agent betting decision.

        Args:
            event: Event dictionary
            intelligence_brief: Intelligence brief text
            agent_context: Agent's current context (bankroll, history, etc.)

        Returns:
            Formatted prompt string
        """
        prompt = f"""
INTELLIGENCE BRIEF:
{intelligence_brief}

EVENT DETAILS:
- Question: {event.get('question')}
- Current YES Price: ${event.get('yes_price', 0):.2f}
- Market Closes: {event.get('close_time')}
- Kalshi Ticker: {event.get('ticker')}

YOUR CONTEXT:
- Current Bankroll: ${agent_context['bankroll']:,.2f}
- Win Rate: {agent_context['win_rate']:.1f}%
- Total PnL: ${agent_context['total_pnl']:,.2f}
- Recent Trades: {agent_context['recent_trades']}

CONSTRAINTS:
- Maximum bet: ${agent_context['bankroll'] * 0.1:,.2f} (10% of bankroll)
- You must provide: decision (YES/NO/ABSTAIN), amount, confidence (0-1), and detailed reasoning

Make your betting decision now based on the intelligence brief and your trading context.
"""
        return prompt

    def _load_agent_context(self, agent_id: str) -> dict[str, Any]:
        """Load agent's current state from database.

        Args:
            agent_id: Agent identifier

        Returns:
            Dictionary with agent context:
                - bankroll: Current bankroll amount
                - win_rate: Win rate percentage
                - total_pnl: Total profit/loss
                - recent_trades: Summary of recent trades
        """
        # TODO: Query database for actual agent state
        # For now, return mock data
        return {
            "bankroll": 1000.0,  # Starting bankroll
            "win_rate": 50.0,  # 50% win rate
            "total_pnl": 0.0,  # No profit/loss yet
            "recent_trades": "No recent trades"
        }

    def _load_persona(self, persona_id: str) -> str:
        """Load persona description from config or defaults.

        Args:
            persona_id: Persona identifier

        Returns:
            Persona description string
        """
        # TODO: Load from config/personas/week_{N}.yaml if needed
        # For now, use default personas
        return DEFAULT_PERSONAS.get(
            persona_id,
            "You are a general prediction market trader."
        )
