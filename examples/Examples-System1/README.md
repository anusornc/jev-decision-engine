# Examples-System1: 6 Real-World LLM Efficiency Use Cases ⚡

ชุดการทดลองและตัวอย่างการใช้งาน **System 1 Decision Engine** ร่วมกับโมเดล **`iapp/OpenThai-SystemOne`** (Live API จาก iApp Technology) เพื่อเพิ่มประสิทธิภาพ ลดค่าใช้จ่าย และลด Latency ในการทำงานร่วมกับ Large Language Models (LLMs) ให้สูงสุด

> 🎯 **หลักการสำคัญ (The Dual-Process Split):**  
> *"อย่าเช่าโมเดลที่มีความสามารถในการคิดวิเคราะห์เชิงลึกที่แพงที่สุดในโลก (System 2 LLM) เพื่อมาตอบคำถามที่เป็นแค่ตัวเลือก, คะแนนความเสี่ยง, หรือคำตอบ ใช่/ไม่ใช่"*  
> ให้ส่งงานตัดสินใจฉับพลันไปที่ **System 1 (< 250ms)** แล้วเหลือเฉพาะงานที่ต้องสร้างข้อความหรือโค้ดเชิงลึกส่งต่อให้ **System 2**

---

## 📊 สรุปผลการทดลองทั้ง 6 Use Cases (Live API Benchmark)

ผลการรันจริงผ่าน Endpoint `https://api.iapp.co.th/v3/store/openthai/systemone`:

| # | Use Case | โจทย์ที่ทดสอบ | การตัดสินใจของ System 1 (ผลจริง) | Latency สด | การประหยัดเทียบกับ LLM ล้วน |
|---|---|---|---|---|---|
| **1** | **Cost-Tiered Routing** | เช็คสถานะพัสดุ `TH10928372` | `sql_api_lookup` (Conf: 96.0%)<br>ต้องการ LLM: **16.2%** | **675 ms** | ประหยัดโทเค็น LLM **100%** (ดึง SQL ตรงทันที) |
| **2** | **Pre-Execution Guardrail** | สั่ง `DROP DATABASE customer_db_prod` | `deny` (Conf: 91.9%)<br>Reversibility: **0.08 / 2.0** | **263 ms** | สกัดกั้นคำสั่งหายนะได้ใน 0.26 วินาที ก่อนหลุดเข้าระบบ |
| **3** | **RAG Relevance Filter** | ถามใบกำกับภาษี แต่ค้นเจอเรื่องคืนสินค้า | `irrelevant` (Conf: 64.9%)<br>นำเข้า Prompt: **6.2%** | **312 ms** | ลดขนาด Context Window ของ LLM ลง **60–80%** |
| **4** | **Context Pruning** | Traceback ขนาดยาว 500 บรรทัดที่แก้แล้ว | `drop_entirely` (Conf: 54.4%)<br>มีประโยชน์อ้างอิง: **15.5%** | **258 ms** | ป้องกัน Context บวมใน Long-running Coding Agent |
| **5** | **Thai Fraud & Emergency** | โอนเงินเข้าบัญชีม้า 35,000 แล้วโดนบล็อก | `online_shopping_fraud` (96.7%)<br>ความเร่งด่วน: **1.99 / 2.0** (อายัด 85%) | **267 ms** | ตรวจจับบัญชีม้าฉับพลัน Trigger ระบบอายัดบัญชีใน 0.27s |
| **6** | **Output Validation** | ฟังก์ชันคำนวณ VAT พร้อมผลรัน Test ผ่าน | `ready_to_deliver` (Conf: 96.0%)<br>Hallucination-free: **70.5%** | **256 ms** | ส่งมอบงานทันทีโดยไม่ต้องเรียก LLM Reflect ซ้ำ 3-5 วินาที |

---

## 🔬 รายละเอียดเชิงลึกของแต่ละ Use Case

### Use Case 1: Cost-Tiered Model Routing (คัดกรองงานก่อนเรียก LLM)
- **โจทย์:** ลูกค้าพิมพ์ถามสถานะพัสดุในแชทบอท e-Commerce: *"พัสดุหมายเลข TH10928372 ตอนนี้อยู่ที่ไหนแล้วครับ รบกวนเช็คให้หน่อย"*
- **ปัญหาของระบบเดิม:** ส่งคำถามเข้า GPT-4o หรือ Claude 3.5 ทุกครั้ง เสียค่าโทเค็น ~$0.015 และรอนาน 2–3 วินาที
- **ผลลัพธ์จาก OpenThai-SystemOne:**
  ```json
  {
    "routing_target": "sql_api_lookup",
    "probabilities": { "sql_api_lookup": 0.9935, "cheap_llm": 0.0038, "frontier_llm": 0.0027 },
    "requires_llm_reasoning": 0.1620,
    "task_complexity": 0.46
  }
  ```
- **ประโยชน์:** เลี้ยวเข้า SQL API ดึงข้อมูลตรงทันที **ประหยัดค่าโทเค็น LLM 100%** สำหรับเคสนี้

---

### Use Case 2: Pre-Execution Safety Guardrail (ตรวจสอบคำสั่งอันตรายใน Shell/DB)
- **โจทย์:** AI Agent กำลังจะรันคำสั่งเชลล์ในเซิร์ฟเวอร์โปรดักชัน: `'DROP DATABASE customer_db_prod; --force'`
- **ปัญหาของระบบเดิม:** เสี่ยงคำสั่งทำลายล้างหลุดไปรันที่ OS Shell หรือต้องให้ LLM อธิบายซ้ำจนช้า
- **ผลลัพธ์จาก OpenThai-SystemOne:**
  ```json
  {
    "safety_action": "deny",
    "confidence": 0.9195,
    "requires_human_approval": 0.6597,
    "reversibility_score": 0.0757
  }
  ```
- **ประโยชน์:** ตรวจจับคำสั่งอันตรายที่มี reversibility ต่ำมาก (0.07) และสั่ง `deny` ทันทีใน **263ms**

---

### Use Case 3: RAG Retrieval Relevance Filter (คัดกรองเอกสารก่อนส่งเข้า Context LLM)
- **โจทย์:** ผู้ใช้ถามเรื่อง *"วิธีขอใบกำกับภาษีย้อนหลัง"* แต่ระบบ Vector Search ดึง Chunk เรื่อง *"เงื่อนไขการคืนสินค้า"* ติดมาด้วย
- **ปัญหาของระบบเดิม:** ยัดทุก Chunk ที่ค้นเจอเข้า Context Window ทำให้ LLM เกิดอาการ Lost-in-the-Middle และเปลืองโทเค็น
- **ผลลัพธ์จาก OpenThai-SystemOne:**
  ```json
  {
    "chunk_relevance": "irrelevant",
    "include_in_prompt": 0.0620,
    "information_gain": 0.3015
  }
  ```
- **ประโยชน์:** สั่งตัด Chunk นี้ทิ้งก่อนประกอบ Prompt ทำให้ Context กระชับ ประหยัดโทเค็นได้ 60–80%

---

### Use Case 4: Long-Session Context Pruning (บีบอัดประวัติการสนทนาของ Agent)
- **โจทย์:** Agent รันสคริปต์แล้วได้ Traceback บั๊กซ้ำซ้อน 500 บรรทัด ซึ่งในรอบถัดไป Agent แก้ไขโค้ดผ่านแล้ว
- **ปัญหาของระบบเดิม:** บันทึกประวัติทุกอย่างไว้จน Context แตะ 128k ส่งผลให้ Agent ตอบช้าลงเรื่อยๆ
- **ผลลัพธ์จาก OpenThai-SystemOne:**
  ```json
  {
    "pruning_action": "drop_entirely",
    "confidence": 0.5442,
    "has_critical_reference_value": 0.1550
  }
  ```
- **ประโยชน์:** ตัดสินใจ `drop_entirely` บล็อกข้อความขยะทิ้งทันที รักษา Context ของ Agent ให้คลีนตลอดการทำงาน

---

### Use Case 5: Thai E-Commerce Fraud & Emergency Triage (ตรวจจับมิจฉาชีพและการฉ้อโกง)
- **โจทย์:** ข้อความร้องทุกข์: *"ช่วยด้วยค่ะ โอนเงินเข้าบัญชีม้า 35,000 บาท ไปซื้อไอโฟนจากเพจปลอม พอโอนเสร็จมันบล็อกเฟสหนีทันที"*
- **ปัญหาของระบบเดิม:** LLM ทั่วไปไม่เข้าใจบริบทสแลงไทย เช่น "บัญชีม้า" หรือ "บล็อกหนี" ทำให้ตอบช้าไป 3–5 วินาที เงินเหยื่อถูกโอนถ่ายออกไปก่อน
- **ผลลัพธ์จาก OpenThai-SystemOne:**
  ```json
  {
    "fraud_type": "online_shopping_fraud",
    "confidence": 0.9671,
    "urgency_level": 1.9912,
    "instant_account_freeze": 0.8504
  }
  ```
- **ประโยชน์:** ความเร่งด่วนระดับวิกฤต (1.99 / 2.0) และความน่าจะเป็นในการอายัดบัญชีสูงถึง **85%** ช่วยให้ระบบ Automation ดำเนินการอายัดได้ในเสี้ยววินาที

---

### Use Case 6: Post-Generation Output Validation (ตรวจเช็คความพร้อมก่อนส่งมอบ)
- **โจทย์:** LLM สร้างโค้ด `calculate_vat` พร้อมผลทดสอบ Unit Test 3 ข้อผ่านหมด
- **ปัญหาของระบบเดิม:** มักต้องเรียก LLM ซ้ำเพื่อทำ Self-reflection ตรวจสอบตัวเอง ซึ่งกินเวลาเพิ่มอีกเท่าตัว
- **ผลลัพธ์จาก OpenThai-SystemOne:**
  ```json
  {
    "readiness_status": "ready_to_deliver",
    "confidence": 0.9601,
    "confidence_score": 1.9841,
    "is_hallucination_free": 0.7052
  }
  ```
- **ประโยชน์:** ปลดล็อกส่งมอบผลงานทันทีใน 256ms โดยไม่ต้องเสียรอบการคำนวณของ Generative LLM เพิ่มเติม

---

## 🚀 วิธีการทดสอบรันด้วยตัวเอง (Run the Experiments)

คุณสามารถรันสคริปต์เพื่อส่งคำขอจริงไปยังเซิร์ฟเวอร์ของ iApp และบันทึกผลการทดสอบสดได้ทันที:

```bash
# ตรวจสอบว่ามี API Key ใน ~/.config/jev/api-key หรือตั้งใน ENV
export IAPP_API_KEY="your-iapp-api-key"

# รันการทดสอบครบทั้ง 6 Use Cases
python3 examples/Examples-System1/run_experiments.py
```

ไฟล์ผลลัพธ์ JSON ฉบับเต็มของแต่ละ Use Case จะถูกสร้างขึ้นในโฟลเดอร์นี้:
- `usecase_1_cost_tiered_routing.json`
- `usecase_2_pre_execution_guardrail.json`
- `usecase_3_rag_relevance_filter.json`
- `usecase_4_context_pruning.json`
- `usecase_5_thai_fraud_triage.json`
- `usecase_6_output_validation.json`
- `benchmark_results.json` (สรุปรวมทั้งหมด)
