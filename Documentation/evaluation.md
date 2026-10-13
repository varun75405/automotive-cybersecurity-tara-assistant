# Empirical Evaluation Framework & Benchmarks

## Automotive Cybersecurity TARA AI Assistant

---

## 1. Prototype Context & Evaluation Overview

> **Academic Prototype & Advisory Disclaimer:**  
> The evaluation framework assesses the retrieval behavior and domain concept presence of the Automotive Cybersecurity TARA Assistant prototype using a predefined benchmark dataset. The reported metrics measure specific retrieval and keyword presence heuristics and do not establish autonomous answer correctness or production certification.

---

## 2. Knowledge Base & Benchmark Dataset

### Source Knowledge Documents
The synthetic automotive knowledge base in `Input_Data/` comprises:
- **6 Source Markdown Documents** (ingested into vector store):
  1. `Input_Data/architecture/sample_vehicle_architecture.md`
  2. `Input_Data/architecture/communication_matrix.md`
  3. `Input_Data/architecture/ecu_inventory.md`
  4. `Input_Data/threat_knowledge/automotive_threat_library.md`
  5. `Input_Data/threat_knowledge/attack_surface_knowledge.md`
  6. `Input_Data/threat_knowledge/mitigation_library.md`
- **70 Structural Sections** parsed from header markers (`#`, `##`, `###`).
- **209 Vector Chunks** indexed into ChromaDB (512 token target, 64 token overlap).

### Benchmark Questions
The evaluation dataset is stored in `Input_Data/evaluation/evaluation_questions.json` and consists of 20 domain questions across 6 categories:
- **Asset Identification:** 4 questions (ECUs, communication interfaces, trust boundaries).
- **Attack Surface Analysis:** 3 questions (OBD-II, IVI, Automotive Ethernet concerns).
- **Threat Scenario Analysis:** 4 questions (CAN injection, replay attacks, OTA threats, sensor manipulation).
- **Mitigation Controls:** 3 questions (firmware signing, AUTOSAR SecOC, hardware HSM).
- **Vehicle Architecture:** 3 questions (OTA data flow, diagnostic UDS routing, gateway filtering).
- **Cybersecurity Requirements:** 3 questions (UDS security access, V2X pseudonym PKI, rollback protection).

---

## 3. Verified Benchmark Results

**Source File:** `Evaluation_Results/evaluation_summary.json`  
**Timestamp of Execution:** `2026-10-11 11:54:08`  
**Active Mode:** `DEMO FALLBACK`

### Summary Metrics Table

| Metric | Measured Score | Metric Definition & Scope |
|---|---|---|
| **Non-Empty Retrieval Rate** | **100.0%** (20/20) | Percentage of queries where ChromaDB returned $\ge 1$ context chunk. Confirms retrieval pipeline connectivity; does **not** independently verify semantic correctness. |
| **Combined Concept Presence** | **67.33%** | Percentage of expected ground-truth domain keywords found in the LLM response OR retrieved context chunks. Keyword presence heuristic. |
| **Measured Query Latency** | **0.03 seconds** (mean: 0.035s) | Local ChromaDB vector query and template lookup time under DEMO FALLBACK mode (arithmetic mean of 20 query timings: 0.035s, rounded to 0.03s). **Not** a real-LLM API generation latency measurement (which typically requires 1.0–3.0s). |

---

## 4. Question-Level Benchmark Breakdown

| Question ID | Category | Query Snippet | Retrieved Chunks | Concept Match | Latency (s) |
|---|---|---|---|---|---|
| Q01 | Asset | Safety-Critical ECUs | 5 | 0.0% | 0.052s |
| Q02 | Asset | Central Gateway Primary Function | 5 | 100.0% | 0.029s |
| Q03 | Asset | Automotive Ethernet Connected ECUs | 5 | 100.0% | 0.024s |
| Q04 | Asset | Vehicle Trust Boundaries | 5 | 100.0% | 0.025s |
| Q05 | Attack Surface | OBD-II Access Requirements | 5 | 100.0% | 0.019s |
| Q06 | Attack Surface | IVI System Attack Surface | 5 | 100.0% | 0.038s |
| Q07 | Attack Surface | Automotive Ethernet Concerns | 5 | 50.0% | 0.057s |
| Q08 | Threat | CAN Message Injection Impact | 5 | 100.0% | 0.022s |
| Q09 | Threat | Replay Attack Preconditions | 5 | 100.0% | 0.020s |
| Q10 | Threat | Cellular Telematics Threat | 5 | 0.0% | 0.025s |
| Q11 | Threat | Sensor Data Manipulation | 5 | 0.0% | 0.029s |
| Q12 | Mitigation | Malicious Firmware Update Control | 5 | 33.3% | 0.027s |
| Q13 | Mitigation | AUTOSAR SecOC Protection | 5 | 0.0% | 0.025s |
| Q14 | Mitigation | Hardware Security Module (HSM) | 5 | 66.7% | 0.022s |
| Q15 | Architecture | OTA Update Data Flow | 5 | 80.0% | 0.027s |
| Q16 | Architecture | OBD-II to Powertrain UDS Routing | 5 | 100.0% | 0.037s |
| Q17 | Architecture | IVI Domain Gateway Routing | 5 | 50.0% | 0.033s |
| Q18 | Requirement | UDS Security Access Requirement | 5 | 66.7% | 0.079s |
| Q19 | Requirement | V2X Privacy Protection PKI | 5 | 100.0% | 0.045s |
| Q20 | Requirement | OTA Rollback Protection Counter | 5 | 100.0% | 0.059s |

---

## 5. Metric Interpretation for Viva Defense

1. **Non-Empty Retrieval Rate vs Answer Correctness:**  
   The 100% Non-Empty Retrieval Rate confirms that ChromaDB successfully indexed and queried the 209 vector chunks for every test prompt. It does not certify that the answer is completely correct. Human review remains mandatory.
2. **Combined Concept Presence:**  
   Measures whether benchmark keywords (e.g., `Secure Boot`, `HSM`, `SecOC`) were retrieved in the context or mentioned in the answer.
3. **Execution Latency:**  
   The measured 0.03s latency reflects local vector search + in-memory dictionary lookup under DEMO FALLBACK mode (arithmetic mean across 20 query timings: 0.035s, rounded to 0.03s). Real API calls to external cloud LLMs involve network round-trips and autoregressive token generation, typically requiring 1.0–3.0 seconds per call.
