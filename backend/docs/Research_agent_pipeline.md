# Research Agent Pipeline Refactor

## Current Implementation (Monolithic)

Currently, the `Analyst` agent is a single entity responsible for the entire research-to-recommendation pipeline.

### Workflow
1. **Input**: `OpportunitySignal` (from Scout)
2. **Process**:
    - Fetches opportunity details.
    - Queries Exa for information.
    - Synthesizes research.
    - Calculates probabilities and EV.
    - Generates a unified `AnalysisReport`.
3. **Output**: Unified `AnalysisReport` produced by the two-agent pipeline.

### Issues
- **Complexity**: The model must handle both creative writing (research synthesis) and precise mathematical structures (trade parameters) in a single context.
- **Reliability**: Deepseek V3 (and other models) struggle to maintain high quality when multitasking between these distinct modes.
- **Design Deviation**: The implementation previously combined two artifacts; the current design uses a single unified `AnalysisReport` with a research-only draft step.

---

## Proposed Pipeline (Dual-Agent)

Refactor the Analyst phase into two specialized agents: **Researcher** and **Recommender**.

### 1. Researcher Agent 🕵️

**Goal**: Gather facts, verify truth, and synthesize information without the pressure of making a trading decision.

- **Trigger**: New `OpportunitySignal`.
- **Primary Tool**: `ExaClient` (Search/Answer).
- **Process**:
    1. Receives Opportunity.
    2. Generates research questions.
    3. Executes searches.
    4. Writes the research section to the unified analysis file.
- **Output Artifact**: `data/analysis/{date}/{ticker}.md`
    - Contains: **Research Synthesis**, **Sources**.
    - *Missing*: Trade fields (Action, Edge, EV) are left empty/pending.

### 2. Recommender Agent ⚖️

**Goal**: Evaluate the research and make a disciplined, mathematically sound trading decision.

- **Trigger**: Completion of Research.
- **Primary Tools**: `calculate_edge`, `calculate_ev`, `check_risk_limits`.
- **Process**:
    1. Reads the analysis draft (file created by Researcher).
    2. Evaluates the evidence quality.
    3. Estimates `true_probability`.
    4. Computes `Edge` and `EV`.
    5. Applies Risk Management rules.
- **Output Artifact**: Updates `data/analysis/{date}/{ticker}.md`
    - Appends/Fills: **Action**, **Confidence**, **Edge**, **EV**, **Suggested Position**, **Reasoning**.

### Benefits
- **Separation of Concerns**: Creativity vs. Logic.
- **Checkpointing**: If the Recommender fails (e.g., JSON error), the expensive Research is saved.
- **Enhanced Accuracy**: The Recommender can "read" the full research text as input, allowing for better "Chain of Thought" reasoning before outputting numbers.
