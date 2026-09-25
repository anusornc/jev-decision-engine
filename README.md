# Jev Decision Engine ⚡

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8+-brightgreen.svg)](https://python.org)
[![Node.js: 18+](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org)
[![Tests: Passing](https://img.shields.io/badge/Tests-100%25%20Passed-success.svg)](#tests)
[![Models](https://img.shields.io/badge/Models-Jev%201.13%20%7C%20OpenThai--SystemOne-orange.svg)](#models)

**Ultra-fast System 1 AI structured decision engine & type-safe DSL for autonomous coding agents.**

Supports both global [TypeSafe Jev AI](https://www.jevai.org) (`typesafe/jev-1.13`) and Thai localized open-weights [OpenThai-SystemOne](https://huggingface.co/iapp/OpenThai-SystemOne) by iApp.

> 📖 **[อ่านคู่มือการใช้งานฉบับเต็มภาษาไทย (Comprehensive User Guide)](./docs/guide.md)** | **[Decision Primitives Reference](./.agents/skills/jev-decision-engine/references/primitives.md)**

---

## 🎯 Highlights

- **⚡ Sub-150ms Single-Pass Inference:** Instant decisions with zero prose, streaming tokens, or conversational fluff.
- **🛡️ 6 Built-in Official Jev Playbooks:** Aligned with [jevai.org/skills](https://www.jevai.org/th/skills) (`tool_guard`, `model_router`, `task_router`, `research_guard`, `completion_review`, `meta_router`).
- **🇹🇭 Dual-Model Support:** Seamless switching between `typesafe/jev-1.13` and `iapp/OpenThai-SystemOne` for native Thai semantics and fraud detection.
- **📐 Host-Language DSL (Python & JavaScript):** Type-checked question sets compiled into a single forward pass with `.gate()`, `.require()`, and deterministic offline `.mock()`.
- **🔌 Universal Agent Skill:** Plugs directly into Google Antigravity CLI/IDE, Claude Code, Cursor, Windsurf, or OpenCodeInterpreter.
- **📦 Zero External Dependencies:** CLI (`evaluate.py`) is written in 100% pure Python standard library (`urllib`, `json`, `argparse`).

---

## 🚀 Quick Start

### 1. Install as an AI Agent Skill

To enable this skill for your AI Coding Assistant (Antigravity, Claude Code, Cursor):

```bash
# Clone directly into your agent's skills directory
git clone https://github.com/anusornc/jev-decision-engine.git ~/.agents/skills/jev-decision-engine
```

Configure your API keys in `~/.bashrc` or `~/.zshrc`:
```bash
export JEV_API_KEY="your-typesafe-jev-api-key"
export IAPP_API_KEY="your-iapp-api-key"   # Optional: for live OpenThai-SystemOne
```

---

### 2. Standalone CLI Usage (`evaluate.py`)

No `pip install` required! Run directly from the command line:

```bash
# Pre-execution safety guardrail before running destructive commands
python3 scripts/evaluate.py \
  --preset tool_guard \
  --state "Command: 'rm -rf /var/data/prod' on production cluster"

# Dynamic model selection based on task complexity
python3 scripts/evaluate.py \
  --preset model_router \
  --state "Task: 'Implement lock-free ring buffer in C++ with memory fences'"

# Pre-completion sanity check before concluding an objective
python3 scripts/evaluate.py \
  --preset completion_review \
  --state "All 15 unit tests pass, documentation written, zero lint errors"

# Native Thai Consumer Protection / Scam Detection
python3 scripts/evaluate.py \
  --model "iapp/OpenThai-SystemOne" \
  --preset thai_complaint \
  --state "โอนเงินซื้อการ์ดจอไป 15,000 บาท ทางร้านบล็อกหนีไม่ส่งของ โทรไม่ติด"
```

Output is fast and structured:
```text
⚡ [typesafe/jev-1.13] Latency: 90 ms (Mock Demo)
-------------------------------------------------------
• [Choice] action              : deny (Confidence: 99.2%)
• [Noul]   requires_human_approval: 97.0% probability of YES
• [Score]  reversibility       : 0.0 - Irreversible (permanent data loss, drop, or service downtime)
-------------------------------------------------------
```

Add `--raw` to output machine-readable JSON for CI/CD pipes and shell automation.

---

### 3. Python Decision DSL

```python
from dsl.python.system1_dsl import decide, choice, noul, score

# 1. Define the decision schema
triage = decide(
    name="support.triage",
    model="iapp/OpenThai-SystemOne",
    ask={
        "dept": choice("Which department should handle this?", {
            "billing": "charges, invoices, refunds",
            "tech": "bugs, outages, system errors",
            "account": "login, password reset, 2FA"
        }).require(min_conf=0.80, fallback="supervisor_escalation"),
        "urgent": noul("Requires immediate human attention?").gate(0.85),
        "severity": score("Severity rating", ["minor", "major", "critical"])
    }
)

# 2. Evaluate state in a single pass (< 150ms)
decision = triage("Customer: 'Double charged $49 on invoice #8812, refund immediately!'")

print(decision.dept)      # -> "billing"
print(decision.urgent)    # -> True (if noul >= 0.85)
print(decision.severity)  # -> 2 ("critical")
```

#### Deterministic Offline Unit Testing (`.mock()`)
```python
# Mock responses without consuming network API quota
triage.mock({
    "dept": {"choice": "billing", "confidence": 0.99},
    "urgent": {"noul": 0.95},
    "severity": {"score": 2, "legend": "critical"}
})

mock_result = triage("Test state")
assert mock_result.urgent is True
triage.clear_mock()
```

---

### 4. JavaScript / TypeScript DSL

```javascript
const { decide, choice, noul, score } = require("./dsl/js/system1_dsl");

const guard = decide({
    name: "agent.pre_execution_guard",
    ask: {
        action: choice("Determine action before running command", {
            allow: "Safe read-only command",
            confirm: "Requires human confirmation",
            deny: "Dangerous or destructive"
        }),
        safeToExecute: noul("Is it safe for automated execution?").gate(0.85)
    }
});

const result = await guard("Command: 'rm -rf / --no-preserve-root'");
if (!result.safeToExecute) {
    console.log("🛑 Execution intercepted by System 1 Guardrail!");
}
```

---

## 🏛️ The 6 Official Playbook Presets

Aligned with [jevai.org/th/skills](https://www.jevai.org/th/skills):

| Preset | Official Mapping | Output Primitives | Decisions / Values |
| :--- | :--- | :--- | :--- |
| **`tool_guard`** | `jev-tool-guard` | `action` (choice), `requires_human_approval` (noul), `reversibility` (score) | `allow`, `confirm`, `review`, `deny` |
| **`model_router`** | `jev-model-router` | `model_tier` (choice), `requires_deep_reasoning` (noul), `complexity_level` (score) | `fast_cheap`, `standard`, `heavy_reasoning` |
| **`task_router`** | `jev-task-router` | `execution_path` (choice), `is_blocked` (noul) | `proceed_fast`, `deep_review`, `split_task`, `block` |
| **`research_guard`** | `jev-research-guard` | `claim_status` (choice), `is_well_supported` (noul), `grounding_score` (score) | `accept`, `verify_more`, `reject` |
| **`completion_review`** | `jev-completion-review` | `completion_status` (choice), `all_requirements_met` (noul), `remaining_risk` (score) | `complete`, `verify_more`, `incomplete` |
| **`meta_router`** | `jev` Router | `recommended_workflow` (choice) | Selects which of the 5 playbooks above applies |

---

## 🌐 Interactive Playground & Local Proxy

Launch the local decision proxy and browser workbench:

```bash
# Start proxy server on http://localhost:8000
python3 playground/proxy.py

# Open playground/index.html in your browser
open playground/index.html
```

---

## 🧪 Tests

Run the full automated verification test suites:

```bash
# Python DSL Verification (13 tests)
python3 tests/test_dsl.py

# Node.js DSL Verification (17 tests)
node tests/test_dsl.js
```

---

## 📂 Repository Structure

```text
jev-decision-engine/
├── SKILL.md                 # Universal Agent Skill manifest
├── README.md                # Project documentation
├── LICENSE                  # MIT License
├── pyproject.toml           # Python packaging specification
├── scripts/
│   └── evaluate.py          # Standalone 0-dependency CLI
├── dsl/
│   ├── python/              # Python Host-Language DSL
│   │   └── system1_dsl.py
│   └── js/                  # JavaScript Host-Language DSL
│       └── system1_dsl.js
├── examples/
│   └── Examples-System1/    # Real-world System 1 LLM optimization benchmarks (6 use cases)
│       ├── README.md
│       ├── run_experiments.py
│       └── *.json
├── playground/              # Web Lab & Local Proxy
│   ├── index.html
│   └── proxy.py
└── tests/                   # Automated test suites
    ├── test_dsl.py
    └── test_dsl.js
```

---

## 📊 Real-World Optimization Benchmarks (`Examples-System1`)

We tested 6 practical architectures where System 1 models optimize LLM agent workflows (cost, latency, safety, context). All benchmarks were executed against live `iapp/OpenThai-SystemOne`:

👉 **[Explore Full Experiments & JSON Payloads](./examples/Examples-System1/README.md)**

| Use Case | Architectural Role | System 1 Decision | Latency | Benefit |
| :--- | :--- | :--- | :--- | :--- |
| **1. Cost-Tiered Routing** | Bypass LLM for structured questions | `sql_api_lookup` (99.3%) | 675 ms (cold) | 100% token savings vs GPT-4/Opus |
| **2. Pre-Execution Guardrail** | Intercept destructive bash commands | `deny` (98.4%) | 263 ms | Halts `rm -rf` before runtime damage |
| **3. RAG Relevance Filter** | Filter low-relevance vector chunks | `irrelevant` (64.9%) | 312 ms | Saves 1,200 prompt tokens / query |
| **4. Context Pruning** | Compress conversational history | `drop_entirely` (54.4%) | 258 ms | Cuts 60% memory bloat |
| **5. Thai Fraud Triage** | Urgent scam classification | `online_shopping_fraud` (99.4%) | 267 ms | Immediate account freeze (`urgent: 1.99/2`) |
| **6. Output Validation** | Hallucination / policy check | `ready_to_deliver` (96.0%) | 256 ms | Delivers in <300ms without 2nd LLM call |

---

## 📄 License

MIT © [Anusorn Chaikaew](https://github.com/anusornc)
