#!/usr/bin/env python3
"""
System 1 Decision DSL: Python Verification & Experiment Suite
"""

import os
import sys
from pathlib import Path

# Add dsl/python to path
sys.path.insert(0, str(Path(__file__).parent.parent / "dsl" / "python"))
from system1_dsl import choice, noul, score, decide

print("\n" + "=" * 75)
print("🐍 เริ่มต้นการทดลอง: System 1 Decision DSL (Python Implementation)")
print("=" * 75)

passed = 0
total = 0

def assert_test(desc, condition):
    global passed, total
    total += 1
    if condition:
        print(f"  ✅ [PASS] {desc}")
        passed += 1
    else:
        print(f"  ❌ [FAIL] {desc}")

# 1. Compilation Test
print("\n▶️ การทดลองที่ 1: การ Compile ชุดคำถามเป็น 1 Single-Pass Payload")
triage = decide(
    name="support.triage",
    model="iapp/OpenThai-SystemOne",
    ask={
        "dept": choice("Which team?", {
            "billing": "charges, invoices, refunds",
            "tech": "bugs, outages",
            "account": "login, access"
        }),
        "urgent": noul("Needs immediate human attention?").gate(0.85),
        "heat": score("Frustration level", ["calm", "frustrated", "angry"])
    },
    on={"low_confidence": "human_review"}
)

assert_test("Runner ถูกสร้างสำเร็จ", callable(triage))
assert_test("คำถาม Choice บรรจุ criteria ครบ", len(triage.ask["dept"].criteria) == 3)
assert_test("คำถาม Noul มี gate = 0.85", triage.ask["urgent"].threshold == 0.85)

# 2. Offline Mocking Test
print("\n▶️ การทดลองที่ 2: Offline Unit Testing ด้วย .mock()")
triage.mock({
    "dept": {"choice": "billing", "confidence": 0.98},
    "urgent": {"noul": 0.92},
    "heat": {"score": 2, "legend": "angry"}
})

mock_res = triage("หักเงินซ้ำ 2 รอบ ขอเงินคืนด่วน")
print(f"   Mock Result: dept={mock_res.dept}, urgent={mock_res.urgent}, heat={mock_res.heat}")
assert_test("Gated urgent เป็น True (0.92 >= 0.85)", mock_res.urgent is True)
assert_test("Dept คืนค่า 'billing'", mock_res.dept == "billing")
assert_test("Raw answer ยังเข้าถึงได้", mock_res.raw["dept"]["choice"] == "billing")

triage.clear_mock()

# 3. Real Calibrated Evaluation
print("\n▶️ การทดลองที่ 3: ประเมินผลข้อความร้องเรียนจริง (Single Forward Pass)")
real_res = triage("โอนเงินซื้อของแล้วเพจบล็อกหนี บัญชีม้า ช่วยด้วยค่ะ")
print(f"   Real Result: dept={real_res.dept}, urgent={real_res.urgent} (Latency: {real_res.meta['elapsed_ms']}ms)")
assert_test("Dept ถูกจำแนกเป็นตัวเลือกใน Criteria", real_res.dept in ["billing", "tech", "account"])
assert_test("Urgent เป็น boolean", isinstance(real_res.urgent, bool))
assert_test("Latency ต่ำกว่า 150ms", real_res.meta["elapsed_ms"] < 150)

# 4. Gating & Fallback Test
print("\n▶️ การทดลองที่ 4: Gating Threshold & Require Fallback")
guard = decide(
    name="guard",
    ask={
        "category": choice("Type of action", {"read": "safe", "drop": "dangerous"}).require(0.90, "supervisor_fallback"),
        "is_safe": noul("Is it safe?").gate(0.95)
    }
)
guard.mock({
    "category": {"choice": "drop", "confidence": 0.65},  # < 0.90
    "is_safe": {"noul": 0.80}                            # < 0.95
})
guard_res = guard("delete table")
print(f"   Fallback Result: category={guard_res.category}, is_safe={guard_res.is_safe}")
assert_test("ความมั่นใจต่ำกว่าเกณฑ์ต้องสลับไปที่ fallback", guard_res.category == "supervisor_fallback")
assert_test("Gated threshold ไม่ถึง 0.95 ต้องได้ False", guard_res.is_safe is False)

# 5. Agent Loop Pre-Execution Test
print("\n▶️ การทดลองที่ 5: Autonomous Agent Pre-Execution Guardrail")
agent_guard = decide(
    name="agent.guard",
    ask={
        "risk": choice("Risk", {"safe_read": "read only", "destructive": "danger"}),
        "auto_run": noul("Allow auto run?").gate(0.90)
    }
)

def run_agent_cmd(cmd):
    chk = agent_guard(cmd)
    if chk.risk == "destructive" or not chk.auto_run:
        return "BLOCKED"
    return "EXECUTED"

r1 = run_agent_cmd("rm -rf /")
r2 = run_agent_cmd("git status")
print(f"   Command 'rm -rf /' -> {r1}")
print(f"   Command 'git status' -> {r2}")
assert_test("คำสั่ง 'rm -rf /' ต้องถูก BLOCKED", r1 == "BLOCKED")
assert_test("คำสั่ง 'git status' ต้องผ่าน EXECUTED", r2 == "EXECUTED")

print("\n" + "=" * 75)
print(f"🏁 ผลลัพธ์: ผ่าน {passed}/{total} ข้อ ({round(passed/total*100)}%) ✅")
print("=" * 75 + "\n")
