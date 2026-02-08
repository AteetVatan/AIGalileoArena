# Galileo Test Audit Report

**Generated**: 2026-02-08  
**Verdict**: FAIL  
**Implementation Level**: PARTIAL  
**Confidence**: 0.85  

---

## Summary

The AIGalileoArena repository implements a sophisticated multi-turn debate evaluation platform with deterministic scoring and evidence discipline, but **fails to meet 3 of 5 core Galileo Test requirements**.

| Requirement | Status |
|-------------|--------|
| Contradiction Cases | ❌ NOT_VERIFIED |
| Evidence Discipline | ✅ VERIFIED |
| Non-Deference | ❌ NOT_VERIFIED |
| Novel/Testable Reasoning | ❌ NOT_VERIFIED |
| Reproducibility | ✅ VERIFIED |

---

## Output JSON

```json
{
  "galileo_test_implemented": false,
  "implementation_level": "PARTIAL",
  "confidence": 0.85,
  "verdict": "FAIL",
  "repo_map": [
    {"path":"backend/app/infra/debate/runner.py","symbols":["DebateController","_phase_independent","_phase_cross_exam","_phase_revision","_phase_dispute","_phase_judge","_call_structured"],"role":"Main FSM-style multi-turn debate controller (646 lines). Orchestrates 6 phases: setup, independent proposals, cross-exam, revision, dispute, judge.","how_invoked":"Called by usecases/run_eval.py via DebateController.run()"},
    {"path":"backend/app/core/domain/scoring.py","symbols":["validate_judge_output","_correctness","_grounding","_calibration","_falsifiable","compute_case_score","model_passes_eval"],"role":"Deterministic scoring engine (143 lines). Pure functions scoring 0-100: correctness (0-50), grounding (0-25), calibration (0-10), falsifiable (0-15).","how_invoked":"Called after judge phase to compute case score breakdown"},
    {"path":"backend/app/infra/debate/prompts.py","symbols":["proposal_prompt","cross_exam_question_prompt","revision_prompt","judge_prompt","_ROLE_INSTRUCTIONS"],"role":"Prompt templates (372 lines) defining Orthodox/Heretic/Skeptic/Judge roles and TOML output schemas.","how_invoked":"Used by runner.py to construct LLM prompts for each debate phase"},
    {"path":"backend/app/infra/debate/schemas.py","symbols":["Proposal","Revision","QuestionsMessage","AnswersMessage","AdmissionLevel","SharedMemo"],"role":"Pydantic schemas for debate phase outputs (149 lines). Defines evidence_used, admission levels, etc.","how_invoked":"Used for TOML parsing/validation in runner.py"},
    {"path":"backend/app/core/domain/schemas.py","symbols":["JudgeDecision","CaseScoreBreakdown","CaseResult","VerdictEnum","DebateRole"],"role":"Core domain schemas (181 lines). Defines verdict enum (SUPPORTED/REFUTED/INSUFFICIENT), scoring breakdown, case results.","how_invoked":"Used across scoring, persistence, and API layers"},
    {"path":"backend/app/infra/db/models.py","symbols":["RunRow","RunMessageRow","RunResultRow","RunEventRow","DatasetRow","DatasetCaseRow"],"role":"SQLAlchemy ORM models (224 lines). Full persistence of runs, messages, results, events.","how_invoked":"Used by repository.py for Postgres persistence"},
    {"path":"backend/datasets/climate_v1.json","symbols":[],"role":"Dataset with 20 cases (climate science claims). Each case has case_id, topic, claim, pressure_score, label, evidence_packets.","how_invoked":"Loaded via API /datasets endpoint"},
    {"path":"backend/tests/test_scoring.py","symbols":["TestValidateJudgeOutput","TestComputeCaseScore","TestModelPassesEval"],"role":"Scoring unit tests (99 lines). Tests correctness penalties, grounding validation, calibration, model pass thresholds.","how_invoked":"pytest tests/test_scoring.py"},
    {"path":"backend/tests/test_debate_runner.py","symbols":["test_turn_order_converging","test_turn_order_diverging","test_early_stop_convergence","test_toml_retry_on_invalid_response"],"role":"Debate runner integration tests (343 lines). Tests FSM phase ordering, TOML parsing, retry logic, fallback handling.","how_invoked":"pytest tests/test_debate_runner.py"}
  ],
  "requirements": {
    "contradiction_cases": {
      "status":"NOT_VERIFIED",
      "evidence":["prompts.py:58-70 (Orthodox 'steelman MAJORITY', Heretic 'steelman MINORITY')", "test_debate_runner.py:97 (E3 labeled 'Contradicting evidence' but not used in authority-contradiction test)"],
      "notes":"The system has Orthodox/Heretic roles that argue FOR/AGAINST claims, but there are NO test cases where the correct answer requires contradicting an 'authority bait' embedded in the prompt. The scorer does not explicitly reward correct contradiction over authority consensus. Datasets have claims with labels but no authority pressure embedded."
    },
    "evidence_discipline": {
      "status":"VERIFIED",
      "evidence":["prompts.py:43-44 ('RULES: Use ONLY the evidence IDs above.')", "prompts.py:213-216 (admission levels: insufficient, uncertain, none)", "scoring.py:53-61 (_grounding function awards 0-25 pts for valid evidence citations)", "scoring.py:32-34 (critical fail on missing EIDs)", "schemas.py:54,65,75,87 (evidence_used/evidence_refs fields in all phase schemas)"],
      "notes":"Strong evidence discipline: prompts require evidence IDs, answers must cite evidence or admit 'INSUFFICIENT', grounding score penalizes missing/invalid citations, critical fail on hallucinated EIDs. AdmissionLevel enum enforces explicit uncertainty acknowledgment."
    },
    "non_deference": {
      "status":"NOT_VERIFIED",
      "evidence":["prompts.py:59 ('Steelman the MAJORITY interpretation' - Orthodox role instruction)", "prompts.py:63-64 ('Steelman the MINORITY / opposing interpretation' - Heretic role)", "scoring.py (no penalty for appeal-to-authority language)", "grep on 'refusal': no results"],
      "notes":"The Heretic role challenges majority views, and Skeptic questions both sides, but there is NO scorer component that explicitly penalizes appeal-to-authority rhetoric or popularity pleasing. No refusal detection/penalty exists."
    },
    "novel_testable_reasoning": {
      "status":"NOT_VERIFIED",
      "evidence":["scoring.py:72-80 (_falsifiable function checks for keywords like 'because', 'however', 'limitation')", "grep on 'hypothesis': no results"],
      "notes":"The _falsifiable scoring component (0-15 pts) rewards specific, limitation-aware reasoning by keyword matching, but there are NO eval cases that require the model to generate a falsifiable hypothesis with a concrete validation/check plan."
    },
    "reproducibility": {
      "status":"VERIFIED",
      "evidence":["scoring.py:1 (docstring: 'Deterministic scoring engine -- pure functions, no IO.')", "runner.py:420 (judge temperature=0.0)", "runner.py:504,521 (agent temperature=0.3 with retry at 0.0)", "db/models.py:118-137,142-167,172-188 (RunMessageRow, RunResultRow, RunEventRow - full persistence)", "README.md:11 ('Deterministic Scoring')"],
      "notes":"Scoring is deterministic (pure functions). Judge uses temperature=0.0. All prompts, messages, and results are persisted to Postgres with timestamps. Run artifacts include judge_json, evidence_used, and full debate transcripts."
    }
  },
  "key_fail_reasons": [
    "No test cases with 'authority bait' where correct answer contradicts consensus (contradiction_cases: NOT_VERIFIED)",
    "No scorer penalty for appeal-to-authority or popularity-pleasing language (non_deference: NOT_VERIFIED)",
    "No refusal penalty when model refuses to answer safe-to-answer questions (non_deference: NOT_VERIFIED)",
    "No eval requiring falsifiable hypothesis generation with validation plan (novel_testable_reasoning: NOT_VERIFIED)",
    "Keyword-based _falsifiable scoring is a weak proxy, not a true falsifiability test"
  ],
  "risk_notes": [
    "PROMPT INJECTION RISK: Prompts inject claim/evidence text directly without sanitization (prompts.py:36-46)",
    "EVALUATOR LEAKAGE: Orthodox role explicitly told to 'Steelman MAJORITY' may bias toward consensus even when wrong",
    "WEAK DETERMINISM: Agent phases use temperature=0.3, only judge uses 0.0; LLM API variability may affect reproducibility",
    "NO VERSION PINNING: Prompt templates are embedded in code, not separately versioned",
    "LABEL LEAKAGE RISK: Ground truth labels stored in same dataset JSON loaded at runtime",
    "CALIBRATION OVERCONFIDENCE: Calibration score caps penalty at 5 points even for grossly overconfident wrong answers"
  ],
  "remediation_plan_if_missing_or_partial": [
    "1. CREATE CONTRADICTION TEST CASES: Add 10+ cases in datasets/ where evidence contradicts an 'authority bait' statement. Location: backend/datasets/authority_contradiction_v1.json",
    "2. ADD AUTHORITY-DEFERENCE SCORER: In scoring.py, add _deference_penalty(reasoning: str) function. Location: backend/app/core/domain/scoring.py:80+",
    "3. ADD REFUSAL DETECTION: In scoring.py, add _refusal_penalty() for safe_to_answer cases. Location: backend/app/core/domain/scoring.py",
    "4. CREATE HYPOTHESIS EVAL CASES: Add dataset requiring falsifiable hypothesis + test criteria. Location: backend/datasets/hypothesis_v1.json",
    "5. ADD FALSIFIABILITY SCORING: Replace keyword-based _falsifiable with structured check. Location: backend/app/core/domain/scoring.py:72-80",
    "6. VERSION PROMPT TEMPLATES: Move prompts to versioned files. Location: backend/prompts/",
    "7. ADD RUN COMPARISON TOOLING: Create compare_runs.py for regression analysis. Location: backend/app/usecases/compare_runs.py",
    "8. FIX TEMPERATURE NON-DETERMINISM: Set all phases to temperature=0.0. Location: backend/app/infra/debate/runner.py:504",
    "9. SANITIZE PROMPT INJECTION: Add input sanitization. Location: backend/app/infra/debate/prompts.py:27-46",
    "10. SEPARATE LABELS FROM EVAL: Load labels at scoring time only. Location: backend/app/usecases/run_eval.py",
    "11. ADD CI INTEGRATION: Add GitHub Actions workflow. Location: .github/workflows/test.yml",
    "12. STRENGTHEN CALIBRATION PENALTY: Increase overconfidence penalty. Location: backend/app/core/domain/scoring.py:64-69"
  ],
  "improvement_ideas_if_full": [],
  "report_md_filename": "galileo_audit_report.md"
}
```

---

## Repo Implementation Map

| File | Role | Key Symbols |
|------|------|-------------|
| `runner.py` | FSM debate controller (646 lines) | `DebateController`, `_phase_*`, `_call_structured` |
| `scoring.py` | Deterministic scoring (143 lines) | `compute_case_score`, `_correctness`, `_grounding`, `_calibration`, `_falsifiable` |
| `prompts.py` | Prompt templates (372 lines) | `proposal_prompt`, `judge_prompt`, `_ROLE_INSTRUCTIONS` |
| `schemas.py` | Debate phase schemas (149 lines) | `Proposal`, `Revision`, `AdmissionLevel` |
| `db/models.py` | Postgres ORM (224 lines) | `RunRow`, `RunMessageRow`, `RunResultRow`, `RunEventRow` |

---

## Requirement-by-Requirement Findings

### A) Contradiction Cases
- **Status**: ❌ NOT_VERIFIED
- **Evidence**:
  - `prompts.py:58-70`: Orthodox/Heretic roles argue FOR/AGAINST claims
  - `test_debate_runner.py:97`: Test data has "Contradicting evidence" but not authority-contradiction cases
- **Findings**: No test cases embed "authority bait" where correct answer must contradict consensus. Scorer does not reward correct contradiction.

### B) Evidence Discipline
- **Status**: ✅ VERIFIED
- **Evidence**:
  - `prompts.py:43-44`: "Use ONLY the evidence IDs above"
  - `prompts.py:213-216`: Admission levels (insufficient/uncertain/none)
  - `scoring.py:53-61`: Grounding score 0-25 pts for valid citations
  - `scoring.py:32-34`: Critical fail on missing EIDs
- **Findings**: Strong evidence discipline with citation requirements and grounding scoring.

### C) Non-Deference
- **Status**: ❌ NOT_VERIFIED
- **Evidence**:
  - `prompts.py:59`: "Steelman the MAJORITY interpretation" (Orthodox)
  - No penalty for appeal-to-authority language in `scoring.py`
  - No refusal detection (grep on 'refusal': 0 results)
- **Findings**: Heretic role challenges consensus but scorer has no deference penalty.

### D) Novel/Testable Reasoning
- **Status**: ❌ NOT_VERIFIED
- **Evidence**:
  - `scoring.py:72-80`: Keyword-based falsifiability
  - grep on 'hypothesis': 0 results
- **Findings**: Keyword matching is weak proxy. No hypothesis generation eval.

### E) Reproducibility
- **Status**: ✅ VERIFIED
- **Evidence**:
  - `scoring.py:1`: "Deterministic scoring engine -- pure functions"
  - `runner.py:420`: Judge temperature=0.0
  - `db/models.py:118-188`: Full Postgres persistence
- **Findings**: Deterministic scoring, fixed judge temperature, full audit trail.

---

## Key Fail Reasons

1. No test cases with 'authority bait' where correct answer contradicts consensus
2. No scorer penalty for appeal-to-authority or popularity-pleasing language
3. No refusal penalty when model refuses to answer safe-to-answer questions
4. No eval requiring falsifiable hypothesis generation with validation plan
5. Keyword-based `_falsifiable` scoring is a weak proxy, not a true falsifiability test

---

## Risk Notes

| Risk | Location | Severity |
|------|----------|----------|
| Prompt Injection | `prompts.py:36-46` | High |
| Evaluator Leakage | Orthodox "Steelman MAJORITY" | Medium |
| Weak Determinism | Agent temp=0.3 | Medium |
| No Version Pinning | Prompts in code | Low |
| Label Leakage | Dataset JSON | Medium |
| Calibration Gap | Max 5pt penalty | Low |

---

## Remediation Plan (12 Fixes Required for PASS)

1. **CREATE CONTRADICTION TEST CASES**: Add 10+ authority-contradiction cases  
   → `backend/datasets/authority_contradiction_v1.json`

2. **ADD AUTHORITY-DEFERENCE SCORER**: Add `_deference_penalty()` function  
   → `backend/app/core/domain/scoring.py:80+`

3. **ADD REFUSAL DETECTION**: Add `_refusal_penalty()` for safe_to_answer cases  
   → `backend/app/core/domain/scoring.py`

4. **CREATE HYPOTHESIS EVAL CASES**: Add falsifiable hypothesis dataset  
   → `backend/datasets/hypothesis_v1.json`

5. **ADD FALSIFIABILITY SCORING**: Replace keyword-based with structured check  
   → `backend/app/core/domain/scoring.py:72-80`

6. **VERSION PROMPT TEMPLATES**: Move prompts to versioned files  
   → `backend/prompts/`

7. **ADD RUN COMPARISON TOOLING**: Create regression analysis tool  
   → `backend/app/usecases/compare_runs.py`

8. **FIX TEMPERATURE NON-DETERMINISM**: Set all phases to temperature=0.0  
   → `backend/app/infra/debate/runner.py:504`

9. **SANITIZE PROMPT INJECTION**: Add input sanitization  
   → `backend/app/infra/debate/prompts.py:27-46`

10. **SEPARATE LABELS FROM EVAL**: Load labels at scoring time only  
    → `backend/app/usecases/run_eval.py`

11. **ADD CI INTEGRATION**: Add GitHub Actions workflow  
    → `.github/workflows/test.yml`

12. **STRENGTHEN CALIBRATION PENALTY**: Increase overconfidence penalty  
    → `backend/app/core/domain/scoring.py:64-69`

---

## Files Scanned

| File | Lines |
|------|-------|
| `backend/app/infra/debate/runner.py` | 646 |
| `backend/app/core/domain/scoring.py` | 143 |
| `backend/app/infra/debate/prompts.py` | 372 |
| `backend/app/infra/debate/schemas.py` | 149 |
| `backend/app/core/domain/schemas.py` | 181 |
| `backend/app/infra/db/models.py` | 224 |
| `backend/tests/test_scoring.py` | 99 |
| `backend/tests/test_debate_runner.py` | 343 |
| `backend/datasets/climate_v1.json` | 29 |
| `README.md` | 111 |

---

## Search Commands Used

```bash
rg -i "galileo" .
rg -i "score" .
rg -i "contradiction" .
rg -i "authority" .
rg -i "evidence" .
rg -i "citation" .
rg -i "reproduce" .
rg -i "temperature" backend/
rg -i "deterministic" .
rg -i "penali" .
rg -i "consensus" .
rg -i "refusal" .
rg -i "hypothesis" .
rg -i "appeal" .
rg -i "majority" .
```
