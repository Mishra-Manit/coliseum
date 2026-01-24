# Research Agent Pipeline Refactor

## Current Implementation (Monolithic)

Currently, the `Analyst` agent is a single entity responsible for the entire research-to-recommendation pipeline.

### Workflow
1. **Input**: `OpportunitySignal` (from Scout)
2. **Process**:
    - Fetches opportunity details.
    - Uses OpenAI's WebSearchTool for web research.
    - Synthesizes research with embedded sources.
    - Calculates probabilities and EV.
    - Appends research and recommendation to opportunity file.
3. **Output**: Single opportunity file with research and recommendation sections.

### Issues (Resolved)
- **Complexity**: ✅ Solved by splitting into Researcher and Recommender agents
- **Reliability**: ✅ Each agent now focuses on a single task (research vs. evaluation)
- **Design**: ✅ Progressive enrichment model - single opportunity file appended by each stage

---

## Proposed Pipeline (Dual-Agent)

Refactor the Analyst phase into two specialized agents: **Researcher** and **Recommender**.

### 1. Researcher Agent 🕵️

**Goal**: Gather facts, verify truth, and synthesize information without the pressure of making a trading decision.

- **Model**: OpenAI GPT-5-Mini
- **Trigger**: New `OpportunitySignal` from Scout.
- **Primary Tool**: `WebSearchTool()` (Native PydanticAI tool using OpenAI's web search).
- **Process**:
    1. Loads the opportunity file for the market.
    2. Generates 4-8 specific research questions.
    3. Executes web searches using WebSearchTool.
    4. Synthesizes research with embedded sources section.
    5. Appends the research section to the opportunity file.
- **Output Artifact**: `data/opportunities/{ticker}.md` (appended)
    - Contains: **Research Synthesis** (500-1200 words), **Sources** (embedded at bottom).
    - *Missing*: Trade fields (Action, Edge, EV) are left empty/pending.

### 2. Recommender Agent ⚖️

**Goal**: Evaluate the research and make a disciplined, mathematically sound trading decision.

- **Model**: (Uses primary LLM - Claude Sonnet 4)
- **Trigger**: Completion of Research (opportunity file updated with research section).
- **Primary Tools**: `read_opportunity_research`, `calculate_edge`, `calculate_ev`, `check_risk_limits`.
- **Process**:
    1. Reads the opportunity file (updated by Researcher).
    2. Extracts research synthesis and sources.
    3. Evaluates the evidence quality.
    4. Estimates `true_probability`.
    5. Computes `Edge` and `EV`.
    6. Applies Risk Management rules.
    7. Appends recommendation section to opportunity file.
- **Output Artifact**: Updates `data/opportunities/{ticker}.md` (appended)
    - Appends: **Trade Evaluation** table with metrics, **Reasoning**, **Position Sizing**.
    - Frontmatter fields: `action`, `edge`, `expected_value`, `estimated_true_probability`, etc.

### Benefits
- **Separation of Concerns**: Research (creative synthesis) vs. Evaluation (mathematical reasoning).
- **Checkpointing**: If the Recommender fails, the expensive Research is saved in the opportunity file.
- **Enhanced Accuracy**: The Recommender can read the full research text as input before making decisions.
- **Single-file audit trail**: All stages (Scout → Researcher → Recommender) live in one opportunity file.
- **Direct trader handoff**: Final recommendation is handed directly to Trader (no queue).
- **Simplified architecture**: Native WebSearchTool eliminates external research API dependency.
- **Cost-effective**: GPT-5-Mini provides sufficient research quality at lower cost.
