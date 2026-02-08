# AutoGen Integration for AIGalileoArena

Leverage Microsoft AutoGen 0.4's agentic framework to enhance the multi-agent debate system with built-in orchestration, memory, and tool-use capabilities.

## User Review Required

> [!IMPORTANT]
> **Breaking Changes**: This integration will require significant refactoring of the debate controller. The current custom FSM implementation in `runner.py` will be replaced with AutoGen's agent orchestration.

> [!CAUTION]
> **API Cost Implications**: AutoGen's agent-to-agent communication may increase LLM calls. Consider configuring conversation limits and token budgets.

---

## Current Architecture vs. AutoGen Benefits

| Current Custom Implementation | AutoGen 0.4 Enhancement |
|-------------------------------|-------------------------|
| Manual FSM-style phase control | **GraphFlow** - declarative conversation graphs |
| Hardcoded 3-agent + judge roles | **AssistantAgent** with dynamic personas |
| No agent memory between debates | **Persistent memory** for learning patterns |
| No tool use (pure prompt/response) | **Tool integration** for evidence retrieval |
| Custom retry logic | **Built-in structured output** with retries |
| No human-in-the-loop | **UserProxyAgent** for intervention |

---

## Proposed Changes

### Component 1: Core AutoGen Agents Layer

#### [NEW] [autogen_agents.py](file:///s:/SYNC/programming/AIGalileoArena/backend/app/infra/debate/autogen_agents.py)

Create AutoGen agent definitions for debate roles (all using the **same model** being evaluated):

```python
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat

def create_debate_team(model_client, claim: str, evidence: list):
    """Create all agents using the same model_client for fair evaluation."""
    
    # All agents share the same LLM (the one being evaluated)
    orthodox_agent = AssistantAgent(
        name="Orthodox",
        system_message=ORTHODOX_SYSTEM_PROMPT.format(claim=claim),
        model_client=model_client,  # Same model
    )

    heretic_agent = AssistantAgent(
        name="Heretic", 
        system_message=HERETIC_SYSTEM_PROMPT.format(claim=claim),
        model_client=model_client,  # Same model
    )

    skeptic_agent = AssistantAgent(
        name="Skeptic",
        system_message=SKEPTIC_SYSTEM_PROMPT.format(claim=claim),
        model_client=model_client,  # Same model
    )

    judge_agent = AssistantAgent(
        name="Judge",
        system_message=JUDGE_SYSTEM_PROMPT,
        model_client=model_client,  # Same model
    )
    
    return [orthodox_agent, heretic_agent, skeptic_agent, judge_agent]
```

---

### Component 2: AutoGen Model Client Adapter

#### [NEW] [autogen_model_client.py](file:///s:/SYNC/programming/AIGalileoArena/backend/app/infra/llm/autogen_model_client.py)

Adapt existing LLM clients to AutoGen's `ChatCompletionClient` interface:

```python
from autogen_core.models import ChatCompletionClient

class GalileoModelClient(ChatCompletionClient):
    """Wrap existing BaseLLMClient for AutoGen compatibility."""
    
    def __init__(self, base_client: BaseLLMClient):
        self._client = base_client
    
    async def create(self, messages, **kwargs) -> CreateResult:
        # Convert AutoGen format ↔ existing client format
        ...
```

---

### Component 3: Adversarial Debate Flow with SelectorGroupChat

#### [NEW] [autogen_debate_flow.py](file:///s:/SYNC/programming/AIGalileoArena/backend/app/infra/debate/autogen_debate_flow.py)

> [!IMPORTANT]
> **No Consensus Required**: The agents are adversarial - Orthodox argues FOR, Heretic argues AGAINST, Skeptic challenges BOTH. They do NOT need to agree. The **Judge makes the final decision** after reviewing all arguments.

Replace manual FSM with AutoGen's `SelectorGroupChat` for adversarial debate:

```python
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination

class AdversarialDebateFlow:
    """
    Adversarial multi-agent debate where agents argue opposing positions.
    No consensus is required - the Judge decides based on argument quality.
    """
    
    def __init__(self, model_client, claim: str, evidence: list):
        self.agents = create_debate_team(model_client, claim, evidence)
        self.orthodox, self.heretic, self.skeptic, self.judge = self.agents
    
    async def run(self, claim: str) -> DebateResult:
        result = DebateResult()
        
        # Phase 1: Independent Proposals (parallel, adversarial)
        # Each agent gives their OPPOSING position independently
        proposals = await asyncio.gather(
            self.orthodox.run(f"Argue FOR: {claim}"),
            self.heretic.run(f"Argue AGAINST: {claim}"),
            self.skeptic.run(f"Challenge BOTH sides on: {claim}"),
        )
        
        # Phase 2: Cross-Examination (sequential, adversarial Q&A)
        # Agents question each other - NOT seeking agreement
        cross_exam_chat = SelectorGroupChat(
            participants=[self.orthodox, self.heretic, self.skeptic],
            model_client=self.model_client,
            selector_prompt=CROSS_EXAM_SELECTOR_PROMPT,
            termination_condition=MaxMessageTermination(max_messages=7),
        )
        cross_exam_result = await cross_exam_chat.run(
            task="Cross-examine opposing positions. Ask probing questions."
        )
        
        # Phase 3: Revision (each agent updates independently)
        revisions = await asyncio.gather(
            self.orthodox.run("Revise your position based on cross-exam"),
            self.heretic.run("Revise your position based on cross-exam"),
            self.skeptic.run("Revise your position based on cross-exam"),
        )
        
        # Check for consensus BEFORE Judge phase
        consensus_verdict = self._check_consensus(revisions)
        
        if consensus_verdict:
            # All 3 agents agree - SKIP Judge phase (faster, cheaper)
            return self._build_consensus_result(
                proposals, cross_exam_result, revisions,
                verdict=consensus_verdict,
                confidence=self._average_confidence(revisions),
            )
        
        # Phase 3.5: Dispute (agents still disagree)
        dispute_result = await self._run_dispute_phase()
        
        # Phase 4: Judge Decision (only when no consensus)
        judge_verdict = await self.judge.run(
            task=f"""
            Review the adversarial debate on: {claim}
            
            Orthodox argued FOR, Heretic argued AGAINST, Skeptic challenged both.
            They could NOT reach consensus - you must decide.
            
            Evaluate argument quality and evidence, then render your verdict.
            """
        )
        
        return self._build_result(proposals, cross_exam_result, revisions, judge_verdict)
    
    def _check_consensus(self, revisions) -> Optional[str]:
        """Return verdict if all 3 agents agree, else None."""
        verdicts = [r.verdict for r in revisions]
        if len(set(verdicts)) == 1:
            return verdicts[0]  # Unanimous agreement
        return None  # No consensus - need Judge
    
    def _average_confidence(self, revisions) -> float:
        """Average confidence when consensus is reached."""
        return sum(r.confidence for r in revisions) / len(revisions)
```

**Key Design Points:**
- **Adversarial by design**: Orthodox ≠ Heretic (opposite positions)
- **Skeptic challenges both**: Not a tiebreaker, but a stress-tester
- **Consensus skips Judge**: If all 3 agree → use their verdict (faster, cheaper)
- **Judge only when needed**: Resolves disputes when agents disagree

---

### Component 4: Evidence Retrieval Tools

#### [NEW] [autogen_tools.py](file:///s:/SYNC/programming/AIGalileoArena/backend/app/infra/debate/autogen_tools.py)

Add tool-use capabilities for agents to actively query evidence:

```python
from autogen_agentchat.tools import FunctionTool

@FunctionTool
def get_evidence(eid: str) -> str:
    """Retrieve evidence packet by ID."""
    ...

@FunctionTool
def search_evidence(query: str) -> list[dict]:
    """Semantic search across evidence packets."""
    ...

@FunctionTool
def validate_citation(eid: str, claim: str) -> dict:
    """Check if evidence supports the specific claim."""
    ...
```

---

### Component 5: Integration with Existing Runner

#### [MODIFY] [runner.py](file:///s:/SYNC/programming/AIGalileoArena/backend/app/infra/debate/runner.py)

Add new `AutoGenDebateController` alongside existing `DebateController`:

```python
class AutoGenDebateController:
    """AutoGen-powered debate orchestrator."""
    
    async def run(self, *, case_id, claim, topic, evidence_packets, ...):
        # Configure agents with case context
        team = self._build_debate_team(claim, topic, evidence_packets)
        
        # Run the structured debate
        result = await team.run(task=f"Evaluate claim: {claim}")
        
        # Extract judge verdict
        return self._parse_result(result)
```

---

### Component 6: Feature Flag for Gradual Rollout

#### [MODIFY] [config.py](file:///s:/SYNC/programming/AIGalileoArena/backend/app/config.py)

Add configuration to toggle between implementations:

```python
class Settings(BaseSettings):
    # ... existing settings ...
    use_autogen_debate: bool = False  # Feature flag
    autogen_max_rounds: int = 10      # Conversation limit
    autogen_enable_tools: bool = True # Tool-use toggle
```

---

## Single-LLM Evaluation Model

> [!NOTE]
> **One LLM per run**: Since the purpose is to evaluate a specific model, all agents (Orthodox, Heretic, Skeptic, Judge) use the **same LLM** in each execution. This tests how well a single model can argue both sides and judge impartially.

## Expected Improvements

| Improvement | Description |
|-------------|-------------|
| **Dynamic Conversation** | Agents can ask follow-up questions naturally instead of fixed 7-step cross-exam |
| **Tool Use** | Agents can query evidence mid-conversation, improving grounding |
| **Better Early Stopping** | Automatic convergence detection via AutoGen's termination conditions |
| **Structured Output** | Built-in JSON/TOML schema enforcement with retries |
| **Observability** | AutoGen's native logging and tracing for debugging |
| **Consistent Evaluation** | All agents use same model, ensuring fair single-model assessment |

---

## Verification Plan

### Automated Tests

Run existing unit tests to ensure no regressions in current implementation:

```powershell
cd S:\SYNC\programming\AIGalileoArena\backend
.venv\Scripts\Activate.ps1
pytest tests/ -v
```

Key test files:
- `test_debate_runner.py` - Debate flow validation
- `test_scoring.py` - Score calculation
- `test_toml_serde.py` - Output parsing

### New Integration Tests

After implementation, add new tests:

```powershell
pytest tests/test_autogen_debate.py -v
```

### Manual Verification

1. **Feature Flag Off**: Verify existing behavior unchanged via API:
   ```powershell
   curl http://localhost:8000/health
   curl http://localhost:8000/datasets
   ```

2. **Feature Flag On**: Run a single case with AutoGen enabled:
   - Set `USE_AUTOGEN_DEBATE=true` in `backend/.env`
   - Start backend: `uvicorn app.main:app --reload`
   - Trigger evaluation via frontend or Swagger docs
   - Compare judge output quality with current implementation

---

## Implementation Order

1. Create `autogen_model_client.py` adapter
2. Create `autogen_agents.py` with role definitions
3. Create `autogen_debate_flow.py` with GraphFlow
4. Create `autogen_tools.py` for evidence retrieval
5. Add feature flag to `config.py`
6. Create `AutoGenDebateController` in `runner.py`
7. Wire up in `run_eval.py` with feature flag check
8. Add integration tests
