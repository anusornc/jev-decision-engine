---
name: jev-decision-engine
description: >-
  Ultra-fast System 1 structured decision-making engine powered by Jev Model (typesafe/jev-1.13)
  and OpenThai-SystemOne (iapp/OpenThai-SystemOne).
  Use this skill when you need sub-150ms type-safe decisions without verbose prose, including:
  (1) Tool guardrails before running risky bash/database commands (Official jev-tool-guard: allow, confirm, review, deny),
  (2) Dynamic model selection (Official jev-model-router: fast_cheap, standard, heavy_reasoning),
  (3) Task flow control (Official jev-task-router: proceed_fast, deep_review, split_task, block),
  (4) Factual claim grounding check (Official jev-research-guard: accept, verify_more, reject),
  (5) Objective completion verification (Official jev-completion-review: complete, verify_more, incomplete),
  (6) Intent classification, customer support triage, content moderation, or agent context pruning.
---

# Jev Decision Engine (System 1 AI)

This skill equips the agent with an autonomous **System 1 Decision Engine** powered by `typesafe/jev-1.13` and `iapp/OpenThai-SystemOne`. It provides instant (~100ms), zero-prose, type-safe decision making across three primitives: **Choice**, **Score**, and **Noul**.

---

## When to Use This Skill

1. **Before Executing Consequential Tools (`tool_guard`):** Before running destructive commands (`rm`, `drop`, `kill`, `git reset --hard`, `sudo`). Check action (`allow`, `confirm`, `review`, `deny`).
2. **Dynamic Model Routing (`model_router`):** Deciding whether a task needs a fast/cheap model, standard model, or heavy reasoning model.
3. **Task Pathway Steering (`task_router`):** Choosing whether to `proceed_fast`, do a `deep_review`, `split_task`, or `block`.
4. **Factual Grounding Check (`research_guard`):** Validating a research claim against evidence in hand before treating it as established fact (`accept`, `verify_more`, `reject`).
5. **Objective Completion Review (`completion_review`):** Pre-completion check before concluding an objective (`complete`, `verify_more`, `incomplete`).
6. **Domain Presets:**
   - `triage`: Customer support intent and urgency triage.
   - `moderation`: Policy violation and auto-ban detection.
   - `pruning`: History compaction (drop, summarize, keep verbatim).
   - `thai_complaint`: Thai consumer complaint classification (fraud, late delivery, damage).

---

## Quick Start CLI Usage

The executable script is located at [evaluate.py](./scripts/evaluate.py) (uses 100% Python Standard Library, zero external pip dependencies).

### 1. Using Official Jev Playbook Presets

```bash
# 1. Tool Guardrail (allow / confirm / review / deny)
python3 .agents/skills/jev-decision-engine/scripts/evaluate.py \
  --preset tool_guard \
  --state "Command: 'rm -rf /var/log/app/*' on production server"

# 2. Model Router (fast_cheap / standard / heavy_reasoning)
python3 .agents/skills/jev-decision-engine/scripts/evaluate.py \
  --preset model_router \
  --state "Task: 'Implement lock-free ring buffer in C++ with memory fences'"

# 3. Task Router (proceed_fast / deep_review / split_task / block)
python3 .agents/skills/jev-decision-engine/scripts/evaluate.py \
  --preset task_router \
  --state "Refactor entire legacy monolith into 25 microservices"

# 4. Research Guard (accept / verify_more / reject)
python3 .agents/skills/jev-decision-engine/scripts/evaluate.py \
  --preset research_guard \
  --state "Claim: 'Quantum dots improve OLED efficiency by 40%', source: Nature Photonics paper"

# 5. Completion Review (complete / verify_more / incomplete)
python3 .agents/skills/jev-decision-engine/scripts/evaluate.py \
  --preset completion_review \
  --state "All 15 unit tests pass, documentation written, zero lint errors"

# 6. Meta Router (determines which specialized playbook to invoke)
python3 .agents/skills/jev-decision-engine/scripts/evaluate.py \
  --preset meta_router \
  --state "Reviewing paper citations for medical claim"
```

### 2. Thai Localized Model (`iapp/OpenThai-SystemOne`)

```bash
python3 .agents/skills/jev-decision-engine/scripts/evaluate.py \
  --model "iapp/OpenThai-SystemOne" \
  --preset tool_guard \
  --state "คำสั่ง: rm -rf /data/prod บนเซิร์ฟเวอร์หลัก"
```

### 3. Custom Multi-Primitive Evaluation

You can specify custom questions directly via flags:

```bash
python3 .agents/skills/jev-decision-engine/scripts/evaluate.py \
  --state "User request: 'Can you help me reset my account password?'" \
  --choice "category:auth=Authentication and login,billing=Invoices and payments,general=General inquiry" \
  --noul "needs_human=Does this require human agent verification?" \
  --score "urgency:Low,Medium,High"
```

### 4. Raw JSON Output for Automation

Add `--raw` to get machine-readable JSON for integration into pipelines or shell scripts:

```bash
python3 .agents/skills/jev-decision-engine/scripts/evaluate.py \
  --preset tool_guard \
  --state "Command: 'ls -la'" \
  --raw
```

---

## The 3 Typed Decision Primitives

For in-depth details on each primitive, see [primitives.md](./references/primitives.md).

| Primitive | Return Value | Typical Use Case |
| :--- | :--- | :--- |
| **`choice`** | Option key + probability distribution + confidence | Routing, action selection, categorization |
| **`score`** | Weighted float score (0 to N) + legend | Severity level, urgency, complexity, reversibility |
| **`noul`** | Calibrated probability of True/Yes (0.0 to 1.0) | Human-in-the-loop gate, safety checks, assertions |

---

## Agent Decision Rules & Thresholds

When evaluating results from the engine:
- **Tool Guard Action:**
  - `deny`: **Never execute.** Abort action immediately and inform user.
  - `confirm`: **Halt and prompt user.** Ask explicit user confirmation.
  - `review`: **Inspect parameters.** Clarify or verify scope before proceeding.
  - `allow`: **Safe to proceed.** Execute automatically unattended.
- **Noul Risk Probability:**
  - **`noul >= 0.85`:** High Risk / Confirmation Required. Stop and prompt the user.
  - **`0.40 <= noul < 0.85`:** Ambiguous. Fallback to standard reasoning or clarify with user.
  - **`noul < 0.40`:** Safe. Proceed with automatic unattended execution.
- **Completion Review:**
  - `complete` (`all_requirements_met >= 0.85`): Safe to declare objective finished.
  - `verify_more`: Run sanity check/test before concluding.
  - `incomplete`: Do NOT mark task as complete; address unresolved deliverables.
