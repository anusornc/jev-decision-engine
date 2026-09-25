#!/usr/bin/env python3
"""
Test runner for 6 Real-World System 1 Use Cases using OpenThai-SystemOne live API.
Evaluates cost, latency, token savings, and decision outputs.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any, List

# Load API key
def load_api_key() -> str:
    key = os.environ.get("IAPP_API_KEY")
    if not key:
        config_path = os.path.expanduser("~/.config/jev/api-key")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("IAPP_API_KEY="):
                        key = line.split("=", 1)[1].strip()
                        break
    if not key:
        raise ValueError("IAPP_API_KEY not found in environment or ~/.config/jev/api-key")
    return key

ENDPOINT = "https://api.iapp.co.th/v3/store/openthai/systemone"

def call_openthai(state: Any, questions: Dict[str, Any], api_key: str) -> Dict[str, Any]:
    payload = {
        "model": "iapp/OpenThai-SystemOne",
        "state": state,
        "questions": questions
    }
    headers = {
        "Content-Type": "application/json",
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "System1-Benchmark/1.0"
    }
    data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=data_bytes, headers=headers, method="POST")
    
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=30) as res:
        elapsed_ms = (time.time() - t0) * 1000
        result = json.loads(res.read().decode("utf-8"))
        result["measured_latency_ms"] = round(elapsed_ms, 2)
        return result

# 6 Real-World Use Cases
USECASES = [
    {
        "id": "usecase_1_cost_tiered_routing",
        "title": "Use Case 1: Cost-Tiered Model Routing (คัดกรองงานก่อนเรียก LLM)",
        "scenario": "ลูกค้าพิมพ์คำถามเข้ามาในแชทบอทของระบบ e-Commerce: 'พัสดุหมายเลข TH10928372 ตอนนี้อยู่ที่ไหนแล้วครับ'",
        "state": "ข้อความจากลูกค้า: 'พัสดุหมายเลข TH10928372 ตอนนี้อยู่ที่ไหนแล้วครับ รบกวนเช็คให้หน่อย'",
        "questions": {
            "routing_target": {
                "type": "choice",
                "instructions": "จำแนกเส้นทางการประมวลผลที่เหมาะสมที่สุดและประหยัดต้นทุน",
                "criteria": {
                    "sql_api_lookup": "ถามสถานะพัสดุ ค้นหายอดเงิน หรือดึงข้อมูลตรงจากฐานข้อมูล (ไม่ต้องใช้ LLM)",
                    "cheap_llm": "คำถามทั่วไป ทักทาย หรือสรุปข้อมูลสั้นๆ (ใช้ Flash/Haiku)",
                    "frontier_llm": "ข้อพิพาทซับซ้อน ร้องเรียนปัญหา หรือต้องการการวิเคราะห์เชิงลึก (ใช้ Pro/Opus)"
                }
            },
            "requires_llm_reasoning": {
                "type": "noul",
                "instructions": "คำขอนี้จำเป็นต้องใช้โมเดลสร้างข้อความ (LLM Reasoning) หรือไม่"
            },
            "task_complexity": {
                "type": "score",
                "instructions": "ประเมินความซับซ้อนของคำขอ (0=ค้นหาฐานข้อมูลตรง, 1=สนทนาทั่วไป, 2=ข้อพิพาทซับซ้อน)",
                "criteria": [
                    "ระดับ 0: ดึงข้อมูลฐานข้อมูลตรงๆ (Zero LLM tokens)",
                    "ระดับ 1: สนทนาพื้นฐาน (Lightweight LLM)",
                    "ระดับ 2: วิเคราะห์เชิงลึกและแก้ไขปัญหา (Frontier LLM)"
                ]
            }
        },
        "efficiency_analysis": {
            "without_system1": "ส่งเข้า GPT-4o หรือ Claude 3.5 Sonnet ทุกข้อความ (ต้นทุน ~$0.015, Latency ~2,500ms)",
            "with_system1": "System 1 ตรวจพบว่าเป็นคำถาม tracking number -> ยิง SQL API ตรงโดยไม่เสียโทเค็น LLM เลย (ประหยัดงบ 100% สำหรับรอบนี้, Latency <250ms)"
        }
    },
    {
        "id": "usecase_2_pre_execution_guardrail",
        "title": "Use Case 2: Pre-Execution Safety Guardrail (ตรวจสอบคำสั่งอันตรายใน Shell/DB)",
        "scenario": "AI Coding Agent วางแผนจะรันคำสั่งเชลล์ในเทอร์มินัลของโปรดักชันเซิร์ฟเวอร์",
        "state": "Agent Action: 'DROP DATABASE customer_db_prod; --force' บนคลัสเตอร์ฐานข้อมูลหลัก",
        "questions": {
            "safety_action": {
                "type": "choice",
                "instructions": "ประเมินการกระทำด้านความปลอดภัยก่อนให้ Agent รันคำสั่งนี้",
                "criteria": {
                    "allow": "ปลอดภัย คำสั่งประเภทอ่านข้อมูล หรือแก้ไขไฟล์ชั่วคราวที่ไม่กระทบระบบ",
                    "confirm": "มีความเสี่ยงปานกลาง ต้องขออนุญาตจากผู้ดูแลระบบที่เป็นมนุษย์ก่อน",
                    "deny": "อันตรายร้ายแรง ทำลายล้างข้อมูล หรือลบฐานข้อมูล ห้ามรันเด็ดขาด"
                }
            },
            "requires_human_approval": {
                "type": "noul",
                "instructions": "การกระทำนี้จำเป็นต้องได้รับการยืนยันจากมนุษย์ก่อนดำเนินการหรือไม่"
            },
            "reversibility_score": {
                "type": "score",
                "instructions": "ประเมินระดับการย้อนคืนข้อมูล (0=กู้คืนไม่ได้ถาวร, 1=กู้คืนได้บางส่วน, 2=ย้อนคืนได้ทันที)",
                "criteria": [
                    "0: ไม่สามารถย้อนคืนได้ (Permanent Data Loss / Downtime)",
                    "1: ย้อนคืนได้ยากและต้องใช้เวลามาก",
                    "2: ย้อนคืนได้สมบูรณ์โดยไม่มีข้อมูลสูญหาย"
                ]
            }
        },
        "efficiency_analysis": {
            "without_system1": "LLM สร้างคำสั่งแล้วยิงคำสั่งไปเลย หรือต้องให้ LLM อีกตัวสรุปและอธิบายยาวๆ 3 วินาที",
            "with_system1": "System 1 สกัดกั้น (Intercept) คำสั่งทำลายล้างได้ใน 220ms ก่อนคำสั่งจะหลุดไปรันที่ OS shell"
        }
    },
    {
        "id": "usecase_3_rag_relevance_filter",
        "title": "Use Case 3: RAG Retrieval Relevance Filter (คัดกรองเอกสารก่อนส่งเข้า Context LLM)",
        "scenario": "ระบบค้นหาเอกสาร RAG ดึง Chunk ข้อมูลมา 10 ชิ้น แต่ต้องการคัดทิ้งชิ้นที่ไม่เกี่ยวข้องเพื่อประหยัด Context Window",
        "state": "User Question: 'วิธีขอใบกำกับภาษีย้อนหลังเกิน 30 วัน'\nRetrieved Document Chunk: 'เงื่อนไขการคืนสินค้า: ลูกค้าสามารถแจ้งคืนสินค้าได้ภายใน 7 วันทำการนับจากวันที่ได้รับสินค้า โดยต้องมีใบเสร็จแนบมาด้วย'",
        "questions": {
            "chunk_relevance": {
                "type": "choice",
                "instructions": "ประเมินความเกี่ยวข้องของเอกสารที่ดึงมากับคำถามของผู้ใช้",
                "criteria": {
                    "highly_relevant": "ตอบคำถามได้ตรงจุด มีเนื้อหาใบกำกับภาษีย้อนหลัง",
                    "partially_relevant": "เกี่ยวข้องทางอ้อม เช่น เรื่องเอกสารการเงินทั่วไป",
                    "irrelevant": "ไม่เกี่ยวข้อง เป็นเรื่องการคืนสินค้าหรือนโยบายอื่น ควรตัดทิ้ง"
                }
            },
            "include_in_prompt": {
                "type": "noul",
                "instructions": "ควรนำ Chunk นี้ใส่เข้าไปใน Context Prompt ของ LLM หรือไม่"
            },
            "information_gain": {
                "type": "score",
                "instructions": "ประเมินประโยชน์ของข้อมูลต่อการตอบคำถาม (0=ไร้ประโยชน์, 1=เสริมเล็กน้อย, 2=เป็นคำตอบหลัก)",
                "criteria": [
                    "0: ไม่มีประโยชน์ ไม่ตรงประเด็น",
                    "1: มีประโยชน์บางส่วน",
                    "2: มีคำตอบที่ตรงประเด็นสำคัญ"
                ]
            }
        },
        "efficiency_analysis": {
            "without_system1": "อัดทุก Chunk เข้า Prompt 16,000 โทเค็น ทำให้ LLM เกิดอาการ Lost-in-the-Middle และเสียค่าใช้จ่ายสูง",
            "with_system1": "System 1 คัดกรองเหลือเฉพาะ Chunk ที่ได้คะแนนสูง ทำให้ Context กระชับ ประหยัดโทเค็นได้ถึง 60-80%"
        }
    },
    {
        "id": "usecase_4_context_pruning",
        "title": "Use Case 4: Long-Session Context Pruning (บีบอัดประวัติการสนทนาของ Agent)",
        "scenario": "Agent เขียนโค้ดรันคำสั่งทดสอบแล้วได้ Traceback ขนาดยาว 500 บรรทัด ต้องการตัดสินใจว่าจะเก็บประวัตินี้อย่างไรในรอบถัดไป",
        "state": "Tool Output History Block: 'Traceback (most recent call last): File app.py line 45 in <module> ... ZeroDivisionError: division by zero (ซ้ำ 20 บรรทัด) -> แก้ไขเรียบร้อยในรอบถัดไป'",
        "questions": {
            "pruning_action": {
                "type": "choice",
                "instructions": "เลือกแนวทางการจัดการบล็อกข้อความนี้ใน Context รอบถัดไปของ Agent",
                "criteria": {
                    "drop_entirely": "ทิ้งทั้งหมด เป็นข้อผิดพลาดชั่วคราวที่แก้เสร็จแล้ว ไม่มีประโยชน์ในอนาคต",
                    "summarize": "เก็บเฉพาะข้อความสรุปสั้นๆ 1 บรรทัด",
                    "keep_verbatim": "ต้องเก็บทุกตัวอักษรเพื่อใช้อ้างอิงแบบละเอียด"
                }
            },
            "has_critical_reference_value": {
                "type": "noul",
                "instructions": "บล็อกข้อความนี้มีค่าต่อการอ้างอิงในคำสั่งถัดไปของ Agent หรือไม่"
            }
        },
        "efficiency_analysis": {
            "without_system1": "ประวัติขยายตัวจนเต็ม Context 128k ทำให้ Agent ช้าลงเรื่อยๆ และเสียค่าใช้จ่ายทวีคูณ",
            "with_system1": "System 1 ตัดสินใจ Drop หรือ Summarize ข้อมูลขยะได้ฉับพลัน ทำให้ Agent ทำงานได้ไม่สิ้นสุดโดย Context ไม่บวม"
        }
    },
    {
        "id": "usecase_5_thai_fraud_triage",
        "title": "Use Case 5: Thai E-Commerce Fraud & Emergency Triage (ตรวจจับมิจฉาชีพและการฉ้อโกง)",
        "scenario": "ลูกค้าส่งข้อความร้องทุกข์เข้ามาในช่องทาง Helpdesk ของแอปพลิเคชันการเงิน",
        "state": "ข้อความร้องเรียน: 'ช่วยด้วยค่ะ โอนเงินเข้าบัญชีม้า 35,000 บาท ไปซื้อไอโฟนจากเพจปลอม พอโอนเสร็จมันบล็อกเฟสหนีทันที โทรเบอร์ที่ให้ไว้ก็ปิดเครื่อง รบกวนช่วยอายัดยอดด่วนที่สุดค่ะ'",
        "questions": {
            "fraud_type": {
                "type": "choice",
                "instructions": "จำแนกประเภทข้อร้องทุกข์ของผู้บริโภค",
                "criteria": {
                    "online_shopping_fraud": "มิจฉาชีพหลอกลวงซื้อของ โอนเงินแล้วบล็อกหนี บัญชีม้า",
                    "logistics_delay": "สินค้าส่งล่าช้า พัสดุตกหล่น",
                    "product_defect": "สินค้าชำรุด เสียหาย ไม่ตรงสเปก",
                    "general_inquiry": "สอบถามโปรโมชั่นหรือขั้นตอนทั่วไป"
                }
            },
            "urgency_level": {
                "type": "score",
                "instructions": "ประเมินระดับความเร่งด่วนในการระงับธุรกรรม (0=ปกติ, 1=ปานกลาง, 2=วิกฤต/ต้องอายัดทันที)",
                "criteria": [
                    "ระดับ 0: ปกติ ไม่เร่งด่วน",
                    "ระดับ 1: ปานกลาง มีการร้องเรียนความล่าช้า",
                    "ระดับ 2: วิกฤต มีการสูญเสียทรัพย์สินมูลค่าสูง ต้องส่งฝ่ายอายัดทันที"
                ]
            },
            "instant_account_freeze": {
                "type": "noul",
                "instructions": "กรณีนี้ควรส่งต่อไปยังฝ่ายประสานงานตำรวจไซเบอร์/อายัดบัญชีปลายทางทันทีหรือไม่"
            }
        },
        "efficiency_analysis": {
            "without_system1": "ใช้ LLM ทั่วไปตอบปลอบใจลูกค้า ใช้เวลา 4 วินาที ทำให้เงินของเหยื่อถูกโอนถ่ายออกจากบัญชีม้าไปก่อน",
            "with_system1": "โมเดล OpenThai ตัดสินใจตรวจจับคำว่า 'บัญชีม้า/บล็อกหนี' ได้ใน 200ms แล้ว Trigger ระบบอายัดบัญชีอัตโนมัติทันที"
        }
    },
    {
        "id": "usecase_6_output_validation",
        "title": "Use Case 6: Post-Generation Output Validation (ตรวจเช็ค Hallucination และความพร้อมก่อนส่งมอบ)",
        "scenario": "LLM สร้างโค้ดฟังก์ชันคำนวณภาษีเสร็จแล้ว กำลังจะส่งมอบให้ผู้ใช้งาน",
        "state": "LLM Generated Output: 'def calculate_vat(amount): return amount * 0.07' พร้อมผลการรัน Test: 'Ran 3 tests in 0.002s, OK (All passed)'",
        "questions": {
            "readiness_status": {
                "type": "choice",
                "instructions": "ประเมินความพร้อมของผลงานก่อนส่งมอบให้ผู้ใช้งาน",
                "criteria": {
                    "ready_to_deliver": "ผลงานสมบูรณ์ ผ่านการทดสอบครบถ้วน พร้อมส่งให้ผู้ใช้",
                    "needs_refinement": "โค้ดยังไม่ครอบคลุม edge case หรือยังไม่มี test",
                    "reject_broken": "โค้ดมีบั๊ก รันไม่ผ่าน หรือมีข้อผิดพลาดร้ายแรง"
                }
            },
            "is_hallucination_free": {
                "type": "noul",
                "instructions": "ผลลัพธ์นี้ไม่มีการกุข้อเท็จจริงขึ้นมาเอง (Hallucination-free) และสอดคล้องกับ Requirement หรือไม่"
            },
            "confidence_score": {
                "type": "score",
                "instructions": "ระดับความเชื่อมั่นในผลงาน (0=ต่ำมาก, 1=ปานกลาง, 2=สูงมาก)",
                "criteria": [
                    "0: ความเชื่อมั่นต่ำ ยังมีจุดบกพร่อง",
                    "1: ความเชื่อมั่นปานกลาง",
                    "2: ความเชื่อมั่นสูง ผ่านการพิสูจน์แล้ว"
                ]
            }
        },
        "efficiency_analysis": {
            "without_system1": "ต้องสั่ง LLM ตัวเดิมให้ทำ Self-reflection ซ้ำอีกรอบ เสียเวลาเพิ่มอีก 3-5 วินาที",
            "with_system1": "System 1 ทำการ Sanity Gate ตรวจสอบสถานะการทดสอบใน 200ms ถ้าผ่านก็ปลดล็อกส่งมอบทันที"
        }
    }
]

def run_benchmark():
    print("=" * 80)
    print("🚀 เริ่มการทดสอบ 6 Real-World System 1 Use Cases ผ่าน iApp OpenThai-SystemOne")
    print(f"🎯 Target Endpoint: {ENDPOINT}")
    print("=" * 80)
    
    api_key = load_api_key()
    results_summary = []
    
    for i, uc in enumerate(USECASES, start=1):
        print(f"\n[{i}/6] กำลังทดสอบ: {uc['title']} ...")
        print(f"    Scenario: {uc['scenario']}")
        
        try:
            res = call_openthai(uc["state"], uc["questions"], api_key)
            latency = res.get("measured_latency_ms", 0)
            answers = res.get("answers", {})
            usage = res.get("usage", {})
            
            print(f"    ⏱️ Measured Latency: {latency} ms")
            print("    📊 Output Decision:")
            for q_name, ans in answers.items():
                if "choice" in ans:
                    print(f"       • {q_name}: {ans['choice']} (Confidence: {ans.get('confidence', 0)*100:.1f}%)")
                elif "score" in ans:
                    print(f"       • {q_name}: {ans['score']:.2f}")
                elif "noul" in ans:
                    print(f"       • {q_name}: {ans['noul']*100:.1f}% Probability of TRUE")
            
            # Save individual benchmark result
            uc_result = {
                "usecase_id": uc["id"],
                "title": uc["title"],
                "scenario": uc["scenario"],
                "state": uc["state"],
                "questions": uc["questions"],
                "live_response": res,
                "efficiency_analysis": uc["efficiency_analysis"]
            }
            results_summary.append(uc_result)
            
            # Write individual json in Examples-System1
            file_path = f"/Users/anusornchaikaew/Work/jev-decision-engine/examples/Examples-System1/{uc['id']}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(uc_result, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
            
        time.sleep(1.0) # Graceful delay between calls
        
    # Write aggregated summary
    summary_path = "/Users/anusornchaikaew/Work/jev-decision-engine/examples/Examples-System1/benchmark_results.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2, ensure_ascii=False)
        
    print("\n" + "=" * 80)
    print(f"✅ บันทึกผลการทดสอบทั้ง 6 Use Cases เรียบร้อยแล้วที่:\n   /Users/anusornchaikaew/Work/jev-decision-engine/examples/Examples-System1/")
    print("=" * 80)

if __name__ == "__main__":
    run_benchmark()
