#!/usr/bin/env python3
"""
CLI tool for Jev Model (typesafe/jev-1.13) Decision Engine.
Supports live API execution as well as simulated mock mode.
"""

import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.error

PRESETS = {
    "guard": {
        "description": "Evaluate safety, risk level, and human approval needed for tool/command execution.",
        "questions": {
            "risk_level": {
                "type": "choice",
                "instructions": "Evaluate the risk level of executing this action/command.",
                "criteria": {
                    "safe": "Read-only or harmless operation",
                    "medium": "Modifies temporary files or non-critical state",
                    "critical": "Irreversible deletion, service restart, or database modification"
                }
            },
            "requires_human_approval": {
                "type": "noul",
                "instructions": "Does this action strictly require human operator confirmation before running?",
                "criteria": {
                    "true": "High risk, production impact, or destructive action",
                    "false": "Can be executed automatically"
                }
            },
            "reversibility": {
                "type": "score",
                "instructions": "Rate reversibility of the action (0=Irreversible, 1=Partially reversible, 2=Fully reversible).",
                "criteria": [
                    "Irreversible (permanent data loss or downtime)",
                    "Partially reversible with significant manual effort",
                    "Fully reversible with no data loss"
                ]
            }
        }
    },
    "router": {
        "description": "Route intent and choose optimal model or execution pathway.",
        "questions": {
            "category": {
                "type": "choice",
                "instructions": "Classify the primary category of this task or query.",
                "criteria": {
                    "simple_qa": "Factual question or greeting requiring fast lightweight model",
                    "code_or_data": "Programming, database, or mathematical computation",
                    "deep_reasoning": "Complex architectural design, proof, or multi-step logic"
                }
            },
            "requires_tools": {
                "type": "noul",
                "instructions": "Does completing this task require external tools (filesystem, terminal, search)?"
            }
        }
    },
    "triage": {
        "description": "Triage customer support or incident tickets by urgency and intent.",
        "questions": {
            "intent": {
                "type": "choice",
                "instructions": "Identify the core customer intent.",
                "criteria": {
                    "refund": "Requesting money back or disputing charges",
                    "technical_bug": "Reporting broken feature or error",
                    "inquiry": "General product or pricing question",
                    "cancellation": "Requesting subscription termination"
                }
            },
            "urgency": {
                "type": "score",
                "instructions": "Rate urgency level (0=low, 1=medium, 2=critical/angry).",
                "criteria": [
                    "Low: polite question or general feedback",
                    "Medium: noticeable dissatisfaction or minor blockage",
                    "Critical: revenue loss, demanding immediate refund, or legal threat"
                ]
            },
            "needs_human": {
                "type": "noul",
                "instructions": "Does this case require human agent intervention?",
                "criteria": {
                    "true": "Requires manual financial or managerial discretion",
                    "false": "Can be automated by workflow"
                }
            }
        }
    },
    "moderation": {
        "description": "Detect prohibited content, counterfeit goods, or dangerous claims.",
        "questions": {
            "violation_type": {
                "type": "choice",
                "instructions": "Identify policy violation category.",
                "criteria": {
                    "medical_claims": "Unverified medical or miracle weight-loss claims without approval",
                    "counterfeit": "Fake or pirated branded goods",
                    "prohibited": "Weapons, narcotics, or illegal substances",
                    "clean": "Complies with standard guidelines"
                }
            },
            "auto_ban": {
                "type": "noul",
                "instructions": "Should this listing/content be immediately taken down?"
            }
        }
    },
    "pruning": {
        "description": "Decide whether to keep, summarize, or discard tool history blocks in agent context.",
        "questions": {
            "retention": {
                "type": "choice",
                "instructions": "How should this history block be handled for next prompt context?",
                "criteria": {
                    "drop": "Discard entirely, irrelevant redundant logs",
                    "summarize": "Drop repetitive tracebacks, keep only final result/status",
                    "keep_verbatim": "Keep entire verbatim output for exact reference"
                }
            }
        }
    },
    "thai_complaint": {
        "description": "Thai consumer protection complaint & scam classification (OpenThai-SystemOne).",
        "questions": {
            "complaint_category": {
                "type": "choice",
                "instructions": "จำแนกประเภทข้อร้องเรียนของผู้บริโภค",
                "criteria": {
                    "fraud_scam": "มิจฉาชีพ/หลอกลวงส่งของไม่ตรงปก/ฉ้อโกง",
                    "late_delivery": "สินค้าจัดส่งล่าช้ากว่ากำหนด",
                    "defective_product": "สินค้าชำรุดเสียหายจากการขนส่ง",
                    "customer_inquiry": "สอบถามข้อมูลทั่วไปหรือสถานะพัสดุ"
                }
            },
            "urgency_score": {
                "type": "score",
                "instructions": "ประเมินระดับความเร่งด่วนและความเสียหาย (0: ต่ำ, 1: ปานกลาง, 2: ร้ายแรง/สูญเสียทรัพย์สินมูลค่าสูง)",
                "criteria": [
                    "ต่ำ ไม่มีผลกระทบทางการเงิน",
                    "ปานกลาง สินค้าล่าช้าหรือผิดแบบเล็กน้อย",
                    "ร้ายแรง เข้าข่ายฉ้อโกง/สูญเสียเงินจำนวนมาก"
                ]
            },
            "escalate_legal": {
                "type": "noul",
                "instructions": "ส่งต่อฝ่ายกฎหมาย/ประสานงาน สคบ. และอายัดบัญชีร้านค้าทันทีหรือไม่"
            }
        }
    },
    # --- Official Jev Playbook Presets (jevai.org/th/skills) ---
    "tool_guard": {
        "description": "Pre-execution tool guardrail (Official jev-tool-guard: allow, confirm, review, deny).",
        "questions": {
            "action": {
                "type": "choice",
                "instructions": "Determine safety action before invoking this tool or shell command.",
                "criteria": {
                    "allow": "Safe to invoke within evaluated scope unattended",
                    "confirm": "Requires explicit user confirmation before proceeding",
                    "review": "Inspect context and parameters then evaluate again",
                    "deny": "Unsafe or destructive, do not invoke under any circumstances"
                }
            },
            "requires_human_approval": {
                "type": "noul",
                "instructions": "Does this action strictly require human confirmation before running?"
            },
            "reversibility": {
                "type": "score",
                "instructions": "Rate reversibility of the action (0=Irreversible, 1=Partially reversible, 2=Fully reversible).",
                "criteria": [
                    "Irreversible (permanent data loss, drop, or service downtime)",
                    "Partially reversible with manual intervention",
                    "Fully reversible with zero data loss"
                ]
            }
        }
    },
    "model_router": {
        "description": "Dynamic model selection based on complexity vs cost/latency (Official jev-model-router).",
        "questions": {
            "model_tier": {
                "type": "choice",
                "instructions": "Select the most cost-effective and capable model tier for this task.",
                "criteria": {
                    "fast_cheap": "Simple Q&A, formatting, or greeting (low latency, minimal cost)",
                    "standard": "Standard coding, tool calls, debugging, or document synthesis",
                    "heavy_reasoning": "High-complexity architecture, math proofs, or kernel/concurrency logic"
                }
            },
            "requires_deep_reasoning": {
                "type": "noul",
                "instructions": "Does this task require prolonged chain-of-thought or frontier-grade reasoning?"
            },
            "complexity_level": {
                "type": "score",
                "instructions": "Rate task complexity (0=Trivial, 1=Moderate, 2=High/Expert).",
                "criteria": [
                    "Trivial/Simple (straightforward lookup)",
                    "Moderate (multi-step standard workflow)",
                    "High/Expert (deep reasoning, subtle bugs, or architectural design)"
                ]
            }
        }
    },
    "task_router": {
        "description": "Task execution pathway and flow control (Official jev-task-router: proceed_fast, deep_review, split_task, block).",
        "questions": {
            "execution_path": {
                "type": "choice",
                "instructions": "Choose the optimal execution pathway for the current task.",
                "criteria": {
                    "proceed_fast": "Clear path with unambiguous specifications, proceed immediately",
                    "deep_review": "Ambiguous, risky, or high-stakes requirements, review thoroughly first",
                    "split_task": "Task is multifaceted or oversized, break down into atomic sub-tasks",
                    "block": "Stop immediately; missing critical prerequisites or violates safety policy"
                }
            },
            "is_blocked": {
                "type": "noul",
                "instructions": "Should execution be blocked or halted due to safety or missing inputs?"
            }
        }
    },
    "research_guard": {
        "description": "Factual grounding and claim validation against evidence (Official jev-research-guard: accept, verify_more, reject).",
        "questions": {
            "claim_status": {
                "type": "choice",
                "instructions": "Evaluate whether the claim is established by the provided sources/evidence.",
                "criteria": {
                    "accept": "Claim is fully established and supported by evidence in hand",
                    "verify_more": "Evidence is ambiguous, incomplete, or requires additional source verification",
                    "reject": "Claim is contradicted, unfounded, or contradicted by evidence"
                }
            },
            "is_well_supported": {
                "type": "noul",
                "instructions": "Is the claim sufficiently grounded in the retrieved sources to treat as fact?"
            },
            "grounding_score": {
                "type": "score",
                "instructions": "Rate the strength of evidence backing this claim (0=None, 1=Partial, 2=Direct/Irrefutable).",
                "criteria": [
                    "Unsupported or speculative",
                    "Partially supported with inferences needed",
                    "Directly supported by authoritative citations"
                ]
            }
        }
    },
    "completion_review": {
        "description": "Pre-completion verification before closing objective (Official jev-completion-review: complete, verify_more, incomplete).",
        "questions": {
            "completion_status": {
                "type": "choice",
                "instructions": "Assess if the task objective is completely fulfilled.",
                "criteria": {
                    "complete": "All criteria met, tests pass, deliverable ready to hand over",
                    "verify_more": "Mostly done, but requires sanity testing or validation before closing",
                    "incomplete": "Objective is not finished; key deliverables or error fixes are missing"
                }
            },
            "all_requirements_met": {
                "type": "noul",
                "instructions": "Have all explicit user requirements and acceptance criteria been satisfied?"
            },
            "remaining_risk": {
                "type": "score",
                "instructions": "Rate remaining unresolved risk or debt (0=Zero risk, 1=Minor cosmetic, 2=Blocking bug).",
                "criteria": [
                    "Zero unresolved risk or debt",
                    "Minor cosmetic or non-blocking warnings",
                    "Blocking bugs or unfinished core logic"
                ]
            }
        }
    },
    "meta_router": {
        "description": "Meta-skill tool router to pick which specialized Jev workflow applies (Official jev router).",
        "questions": {
            "recommended_workflow": {
                "type": "choice",
                "instructions": "Select which specialized decision workflow is required at this boundary.",
                "criteria": {
                    "tool_guard": "Before invoking a consequential tool, bash command, or file deletion",
                    "model_router": "When selecting optimal model tier based on task complexity and budget",
                    "task_router": "When determining execution path (fast, review, split, or block)",
                    "research_guard": "When verifying claims or literature findings against cited sources",
                    "completion_review": "Before declaring a non-trivial goal or task complete",
                    "direct_decide": "Custom multi-primitive question set"
                }
            }
        }
    }
}


def build_mock_response(questions, state="", elapsed_ms=110, model="typesafe/jev-1.13"):
    state_lower = (state or "").lower()
    answers = {}
    is_thai_native = "OpenThai" in model

    for q_id, q_data in questions.items():
        q_type = q_data.get("type", "choice")
        if q_type == "choice":
            criteria = q_data.get("criteria", {})
            keys = list(criteria.keys()) if isinstance(criteria, dict) else ["opt_a", "opt_b"]
            
            # Content-aware choice selection
            chosen = keys[0] if keys else "default"
            conf = 0.94
            if q_id == "complaint_category":
                chosen = "fraud_scam" if "fraud_scam" in keys else keys[0]
                conf = 0.991 if is_thai_native else 0.784
            elif q_id == "action":
                if any(w in state_lower for w in ["drop ", "--force", "format ", "rm -rf /", "truncate"]):
                    chosen = "deny" if "deny" in keys else keys[-1]
                    conf = 0.992
                elif any(w in state_lower for w in ["rm ", "delete", "kill", "restart", "deploy", "upgrade", "drop"]):
                    chosen = "confirm" if "confirm" in keys else keys[0]
                    conf = 0.975
                elif any(w in state_lower for w in ["check", "lint", "inspect", "diff", "review"]):
                    chosen = "review" if "review" in keys else keys[0]
                    conf = 0.930
                else:
                    chosen = "allow" if "allow" in keys else keys[0]
                    conf = 0.960
            elif q_id == "model_tier":
                if any(w in state_lower for w in ["hft", "kernel", "concurrency", "lock-free", "c++", "math proof", "architecture", "frontier"]):
                    chosen = "heavy_reasoning" if "heavy_reasoning" in keys else keys[-1]
                elif any(w in state_lower for w in ["code", "python", "sql", "bug", "refactor", "api", "database"]):
                    chosen = "standard" if "standard" in keys else keys[0]
                else:
                    chosen = "fast_cheap" if "fast_cheap" in keys else keys[0]
            elif q_id == "execution_path":
                if any(w in state_lower for w in ["illegal", "leak", "exploit", "drop prod", "malicious", "bypass"]):
                    chosen = "block" if "block" in keys else keys[-1]
                elif any(w in state_lower for w in ["large", "complex", "epic", "multi-part", "overhaul", "split"]):
                    chosen = "split_task" if "split_task" in keys else keys[0]
                elif any(w in state_lower for w in ["ambiguous", "risk", "unclear", "careful", "review"]):
                    chosen = "deep_review" if "deep_review" in keys else keys[0]
                else:
                    chosen = "proceed_fast" if "proceed_fast" in keys else keys[0]
            elif q_id == "claim_status":
                if any(w in state_lower for w in ["unsupported", "fake", "hallucination", "contradicts", "false"]):
                    chosen = "reject" if "reject" in keys else keys[-1]
                elif any(w in state_lower for w in ["partial", "preliminary", "weak", "unverified", "more evidence"]):
                    chosen = "verify_more" if "verify_more" in keys else keys[0]
                else:
                    chosen = "accept" if "accept" in keys else keys[0]
            elif q_id == "completion_status":
                has_clean_pass = any(w in state_lower for w in ["zero error", "no error", "0 error", "without error", "pass", "all tests pass"])
                if any(w in state_lower for w in ["fail", "error", "broken", "unimplemented", "missing", "todo"]) and not has_clean_pass:
                    chosen = "incomplete" if "incomplete" in keys else keys[-1]
                elif any(w in state_lower for w in ["untested", "sanity check", "needs verify", "validation"]):
                    chosen = "verify_more" if "verify_more" in keys else keys[0]
                else:
                    chosen = "complete" if "complete" in keys else keys[0]
            elif q_id == "recommended_workflow":
                if any(w in state_lower for w in ["rm ", "bash", "command", "tool", "drop", "delete", "file"]):
                    chosen = "tool_guard" if "tool_guard" in keys else keys[0]
                elif any(w in state_lower for w in ["model", "llm", "claude", "cost", "tokens", "latency"]):
                    chosen = "model_router" if "model_router" in keys else keys[0]
                elif any(w in state_lower for w in ["claim", "paper", "fact", "source", "cite", "literature"]):
                    chosen = "research_guard" if "research_guard" in keys else keys[0]
                elif any(w in state_lower for w in ["finish", "done", "complete", "ship", "wrap"]):
                    chosen = "completion_review" if "completion_review" in keys else keys[0]
                else:
                    chosen = "task_router" if "task_router" in keys else keys[0]
            elif "risk" in q_id:
                if any(w in state_lower for w in ["rm ", "drop ", "restart", "delete", "kill", "format", "shutdown", "kubectl"]):
                    chosen = "catastrophic_risk" if "catastrophic_risk" in keys else ("critical" if "critical" in keys else keys[-1])
                    conf = 0.998 if not is_thai_native else 0.914
                else:
                    chosen = "safe" if "safe" in keys else keys[0]
            elif "intent" in q_id:
                if any(w in state_lower for w in ["refund", "money back", "คืนเงิน", "charged twice"]):
                    chosen = "refund" if "refund" in keys else keys[0]
                elif any(w in state_lower for w in ["cancel", "ยกเลิก"]):
                    chosen = "cancellation" if "cancellation" in keys else keys[0]
                elif any(w in state_lower for w in ["bug", "error", "fail", "พัง", "เสีย"]):
                    chosen = "technical_bug" if "technical_bug" in keys else keys[0]
            elif "category" in q_id or "model" in q_id or "tier" in q_id:
                if any(w in state_lower for w in ["hft", "memory pool", "lock-free", "concurrency", "c++", "low-level", "deep reasoning", "architecture", "frontier", "large"]):
                    chosen = "frontier_pro" if "frontier_pro" in keys else ("deep_reasoning" if "deep_reasoning" in keys else keys[-1])
                elif any(w in state_lower for w in ["rust", "python", "sql", "code", "database", "api"]):
                    chosen = "code_or_data" if "code_or_data" in keys else keys[0]
                else:
                    chosen = keys[0]
            elif "retention" in q_id:
                if any(w in state_lower for w in ["traceback", "failed", "repeat", "ขยะ", "log"]):
                    chosen = "summarize" if "summarize" in keys else keys[0]

            probs = {}
            for k in keys:
                probs[k] = conf if k == chosen else round((1.0 - conf) / max(1, len(keys) - 1), 3)
            answers[q_id] = {
                "choice": chosen,
                "confidence": conf,
                "probabilities": probs
            }
        elif q_type == "score":
            criteria = q_data.get("criteria", [])
            count = len(criteria) if isinstance(criteria, list) else 3

            # Content-aware scoring
            score_val = 0.0
            conf = 0.88
            if q_id == "urgency_score" and any(w in state_lower for w in ["ตต.", "แกง", "สคบ.", "15,000"]):
                score_val = 2.0 if is_thai_native else 1.45
                conf = 0.965 if is_thai_native else 0.760
            elif "blast_radius" in q_id:
                score_val = 2.96 if not is_thai_native else 2.62
                conf = 0.994 if not is_thai_native else 0.890
            elif "complexity" in q_id or "difficulty" in q_id:
                if any(w in state_lower for w in ["hft", "memory pool", "lock-free", "concurrency", "c++", "kernel", "assembly"]):
                    score_val = float(count - 1)  # Maximum complexity
                elif any(w in state_lower for w in ["crud", "simple", "greeting", "format"]):
                    score_val = 0.0
                else:
                    score_val = 1.0
            elif q_id == "grounding_score":
                claim_ans = answers.get("claim_status", {}).get("choice")
                if claim_ans == "reject" or any(w in state_lower for w in ["unsupported", "fake", "hallucination", "unverified"]):
                    score_val = 0.0
                elif claim_ans == "verify_more" or any(w in state_lower for w in ["partial", "preliminary", "weak"]):
                    score_val = 1.0
                else:
                    score_val = float(count - 1)
            elif q_id == "remaining_risk":
                comp_ans = answers.get("completion_status", {}).get("choice")
                if comp_ans == "incomplete":
                    score_val = float(count - 1)
                elif comp_ans == "verify_more" or any(w in state_lower for w in ["untested", "warning"]):
                    score_val = 1.0
                elif comp_ans == "complete":
                    score_val = 0.0
                elif any(w in state_lower for w in ["fail", "error", "broken", "missing"]):
                    score_val = float(count - 1)
                else:
                    score_val = 0.0
            elif "urgency" in q_id or "risk" in q_id:
                if any(w in state_lower for w in ["immediately", "now", "sue", "ด่วน", "วิกฤต", "crash", "oom", "500"]):
                    score_val = float(count - 1)
                elif any(w in state_lower for w in ["warn", "slow", "ช้า"]):
                    score_val = float(min(1, count - 1))
            elif "reversibility" in q_id:
                act = answers.get("action", {}).get("choice")
                if act == "deny" or any(w in state_lower for w in ["rm ", "drop ", "truncate"]):
                    score_val = 0.0  # Irreversible
                elif act == "confirm":
                    score_val = 1.0
                else:
                    score_val = float(count - 1)

            idx = min(int(round(score_val)), count - 1)
            probs = [conf if i == idx else round((1.0 - conf) / max(1, count - 1), 3) for i in range(count)]
            answers[q_id] = {
                "score": score_val,
                "confidence": conf,
                "probabilities": probs,
                "legend": criteria[idx] if isinstance(criteria, list) and idx < len(criteria) else f"Level {idx}"
            }
        elif q_type == "noul":
            prob = 0.50
            if q_id == "requires_human_approval":
                act = answers.get("action", {}).get("choice")
                if act == "deny":
                    prob = 0.99
                elif act == "confirm":
                    prob = 0.94
                elif act == "review":
                    prob = 0.65
                else:
                    prob = 0.04 if any(w in state_lower for w in ["ls", "cat", "git status"]) else 0.12
            elif q_id == "escalate_legal":
                prob = 0.98 if is_thai_native else 0.81
            elif q_id == "intercept_execution":
                prob = 0.999 if not is_thai_native else 0.935
            elif q_id == "is_blocked":
                prob = 0.99 if answers.get("execution_path", {}).get("choice") == "block" or any(w in state_lower for w in ["illegal", "exploit", "leak", "drop prod"]) else 0.04
            elif q_id == "is_well_supported":
                c_st = answers.get("claim_status", {}).get("choice")
                if c_st == "reject":
                    prob = 0.04
                elif c_st == "verify_more":
                    prob = 0.38
                else:
                    prob = 0.96
            elif q_id == "all_requirements_met":
                comp_st = answers.get("completion_status", {}).get("choice")
                if comp_st == "incomplete":
                    prob = 0.06
                elif comp_st == "verify_more":
                    prob = 0.58
                else:
                    prob = 0.98
            elif q_id == "requires_deep_reasoning":
                m_tier = answers.get("model_tier", {}).get("choice")
                prob = 0.98 if m_tier == "heavy_reasoning" or any(w in state_lower for w in ["hft", "kernel", "concurrency", "lock-free", "proof"]) else 0.12
            # If asking about readiness, health, or safety
            elif any(w in q_id.lower() for w in ["ready", "clean", "good", "pass", "ok", "valid", "safe"]):
                if any(w in state_lower for w in ["clean", "ready", "complete", "synced", "updated", "safe", "zero", "placeholder"]):
                    prob = 0.98
                else:
                    prob = 0.15
            elif any(w in state_lower for w in ["hft", "memory pool", "lock-free", "c++", "rm ", "drop ", "sue", "refund", "crash", "oom", "human", "danger", "urgent"]):
                prob = 0.97
            elif any(w in state_lower for w in ["ls", "cat", "hello", "greeting", "simple"]):
                prob = 0.03
            else:
                prob = 0.85
            answers[q_id] = {
                "noul": prob
            }

    return {
        "model": model,
        "mock": True,
        "result": {
            "answers": answers
        },
        "elapsed_ms": elapsed_ms
    }


def parse_criteria_kv(raw_str):
    criteria = {}
    for item in raw_str.split(","):
        if "=" in item:
            k, v = item.split("=", 1)
            criteria[k.strip()] = v.strip()
        else:
            item = item.strip()
            if item:
                criteria[item] = item
    return criteria


def run_evaluation():
    parser = argparse.ArgumentParser(description="Jev Decision Engine CLI")
    parser.add_argument("--model", "-m", type=str, default="typesafe/jev-1.13", choices=["typesafe/jev-1.13", "iapp/OpenThai-SystemOne"], help="Model identifier (typesafe/jev-1.13 or iapp/OpenThai-SystemOne)")
    parser.add_argument("--state", "-s", type=str, help="State context string or text to evaluate")
    parser.add_argument("--preset", "-p", choices=list(PRESETS.keys()), help="Use a predefined question preset")
    parser.add_argument("--choice", action="append", help="Define a choice question: 'id:opt1=desc,opt2=desc'")
    parser.add_argument("--score", action="append", help="Define a score question: 'id:level0_desc,level1_desc,level2_desc'")
    parser.add_argument("--noul", action="append", help="Define a noul question: 'id=instructions'")
    parser.add_argument("--json-input", "-j", type=str, help="Path to JSON file containing full payload or pass '-' for stdin")
    parser.add_argument("--api-key", type=str, default=os.environ.get("JEV_API_KEY"), help="Jev AI API Key")
    parser.add_argument("--endpoint", type=str, default=os.environ.get("JEV_API_ENDPOINT", "https://www.jevai.org/api/v1/decisions"), help="Jev Decision API URL")
    parser.add_argument("--mock", action="store_true", help="Force mock mode without network request")
    parser.add_argument("--raw", action="store_true", help="Output raw JSON response only")

    args = parser.parse_args()

    # Determine payload
    payload = None
    if args.json_input:
        if args.json_input == "-":
            payload = json.load(sys.stdin)
        else:
            with open(args.json_input, "r", encoding="utf-8") as f:
                payload = json.load(f)
    else:
        if not args.state:
            print("❌ Error: --state or --json-input is required.", file=sys.stderr)
            parser.print_help()
            sys.exit(1)

        questions = {}
        if args.preset:
            questions.update(PRESETS[args.preset]["questions"])

        if args.choice:
            for item in args.choice:
                if ":" in item:
                    q_id, raw_c = item.split(":", 1)
                    questions[q_id.strip()] = {
                        "type": "choice",
                        "instructions": f"Choose best option for {q_id.strip()}",
                        "criteria": parse_criteria_kv(raw_c)
                    }

        if args.score:
            for item in args.score:
                if ":" in item:
                    q_id, raw_c = item.split(":", 1)
                    crit_list = [c.strip() for c in raw_c.split(",") if c.strip()]
                    questions[q_id.strip()] = {
                        "type": "score",
                        "instructions": f"Score {q_id.strip()}",
                        "criteria": crit_list
                    }

        if args.noul:
            for item in args.noul:
                if "=" in item:
                    q_id, instr = item.split("=", 1)
                    questions[q_id.strip()] = {
                        "type": "noul",
                        "instructions": instr.strip()
                    }
                else:
                    questions[item.strip()] = {
                        "type": "noul",
                        "instructions": f"Is {item.strip()} true?"
                    }

        if not questions:
            print("❌ Error: At least one question (--preset, --choice, --score, --noul) is required.", file=sys.stderr)
            sys.exit(1)

        payload = {
            "model": args.model,
            "state": args.state,
            "questions": questions
        }

    # Execute
    start_time = time.time()
    api_key = args.api_key
    target_model = payload.get("model", args.model)
    is_open_thai = "OpenThai" in target_model
    is_using_jev_cloud = "jevai.org" in args.endpoint

    if args.mock or not api_key or (is_open_thai and is_using_jev_cloud):
        if is_open_thai and is_using_jev_cloud and not args.mock and api_key:
            print("💡 [Notice] 'iapp/OpenThai-SystemOne' is an open-weights model on Hugging Face.", file=sys.stderr)
            print("   TypeSafe's jevai.org cloud API only accepts Jev models (e.g. typesafe/jev-1.13).", file=sys.stderr)
            print("   Running evaluation via calibrated simulated engine.\n", file=sys.stderr)
        time.sleep(0.08)  # simulate ~80ms System 1 inference
        elapsed_ms = round((time.time() - start_time) * 1000)
        data = build_mock_response(payload.get("questions", {}), state=payload.get("state", ""), elapsed_ms=elapsed_ms, model=target_model)
    else:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(args.endpoint, data=req_data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                elapsed_ms = round((time.time() - start_time) * 1000)
                res_body = response.read().decode("utf-8")
                data = json.loads(res_body)
                data["elapsed_ms"] = elapsed_ms
                data["mock"] = False
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            print(f"❌ HTTP Error {e.code}: {err_body}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"❌ Connection Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Output
    if args.raw:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        answers = data.get("result", {}).get("answers", {})
        mode_str = "Mock Demo" if data.get("mock") else "Live API"
        target_model = payload.get("model", args.model)
        print(f"\n⚡ [{target_model}] Latency: {data.get('elapsed_ms')} ms ({mode_str})")
        print("-" * 55)
        for q_id, ans in answers.items():
            if "choice" in ans:
                conf = ans.get("confidence", 0) * 100
                print(f"• [Choice] {q_id:20}: {ans['choice']} (Confidence: {conf:.1f}%)")
            elif "score" in ans:
                legend = f" - {ans.get('legend')}" if ans.get('legend') else ""
                print(f"• [Score]  {q_id:20}: {ans['score']}{legend}")
            elif "noul" in ans:
                prob = ans.get("noul", 0) * 100
                print(f"• [Noul]   {q_id:20}: {prob:.1f}% probability of YES")
        print("-" * 55)
        print("Raw JSON available with --raw flag.\n")


if __name__ == "__main__":
    run_evaluation()
