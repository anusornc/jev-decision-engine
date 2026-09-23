# Jev Decision Primitives Reference

Jev Model (`typesafe/jev-1.13`) operates on 3 fundamental typed decision primitives:

---

## 1. Choice Primitive (`choice`)

### Definition
Selects exactly one option from a predefined finite hypothesis set and returns calibrated probabilities for all options.

### Structure
```json
{
  "type": "choice",
  "instructions": "Clarifying question or intent classification instruction",
  "criteria": {
    "key_1": "Description of condition 1",
    "key_2": "Description of condition 2"
  }
}
```

### Result Schema
```json
{
  "choice": "key_1",
  "confidence": 0.942,
  "probabilities": {
    "key_1": 0.942,
    "key_2": 0.058
  }
}
```

### Best Used For
- Fast intent routing (FAQ vs. DB vs. Agent)
- Model router (Frontier vs. Standard vs. Nano)
- Policy classification (Clean vs. Violation vs. Counterfeit)

---

## 2. Score Primitive (`score`)

### Definition
Evaluates a weighted numerical score across ordered levels (typically 0 to N).

### Structure
```json
{
  "type": "score",
  "instructions": "Rate urgency or severity level",
  "criteria": [
    "Level 0: Safe or low urgency",
    "Level 1: Moderate risk or warning",
    "Level 2: Critical or immediate action required"
  ]
}
```

### Result Schema
```json
{
  "score": 2.0,
  "legend": "Level 2: Critical or immediate action required",
  "probabilities": [0.02, 0.08, 0.90],
  "confidence": 0.90
}
```

### Best Used For
- Incident severity rating (SEV1, SEV2, SEV3)
- Command reversibility score (0=Irreversible, 2=Reversible)
- Customer sentiment/anger level

---

## 3. Noul Primitive (`noul`)

### Definition
Computes the calibrated probability of a binary assertion being true (Probability of Yes/True).

### Structure
```json
{
  "type": "noul",
  "instructions": "Does this action strictly require human operator confirmation before running?",
  "criteria": {
    "true": "High risk, production impact, or destructive action",
    "false": "Can be executed automatically"
  }
}
```

### Result Schema
```json
{
  "noul": 0.965
}
```

### Decision Threshold Rules
- `noul >= 0.85`: **High Confidence True** &rarr; Trigger safety gate / require human approval.
- `0.40 <= noul < 0.85`: **Uncertainty Zone** &rarr; Request step-up confirmation or fallback to System 2 LLM.
- `noul < 0.40`: **High Confidence False** &rarr; Safe for automatic unattended execution.
