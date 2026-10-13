# Presentation & Demo Script (8-10 Minutes)

## Automotive Cybersecurity TARA AI Assistant

---

## 1. Prototype Context & Presentation Setup

> **Academic Prototype & Advisory Disclaimer:**  
> The Automotive Cybersecurity TARA Assistant is an academic engineering prototype developed for the Tata Technologies TechPulse capstone initiative. It is informed by **ISO/SAE 21434 and UNECE R155 concepts**, but does not claim formal compliance, certification, or production readiness. All AI outputs are advisory and require qualified human review.

1. **Launch Streamlit Web App:**
   ```powershell
   cd C:\TARA
   python -m streamlit run frontend/streamlit_app.py
   ```
2. Open browser to `http://localhost:8501`.
3. Verify sidebar mode indicator (`REAL LLM` green badge or `DEMO FALLBACK` orange badge).

---

## 2. Step-by-Step Presentation Script

### Stage 1: Introduction & System Dashboard (1 min)
- **Visual:** Main Streamlit Dashboard (`streamlit_app.py`).
- **Talking Point:** *"This is the Automotive Cybersecurity TARA Assistant, an academic engineering prototype developed for the TechPulse capstone project. It assists cybersecurity engineers by exploring how Retrieval-Augmented Generation (RAG) and deterministic risk scoring can structure TARA workflows informed by ISO/SAE 21434 concepts."*
- **Highlight:** The prominent advisory disclaimer, system status cards, and transparent LLM mode badge.

### Stage 2: Knowledge Ingestion & Vector Indexing (1.5 min)
- **Visual:** Pages `01_Document_Upload.py` and `02_Knowledge_Base.py`.
- **Action:** Click **"Load Sample Data"**.
- **Talking Point:** *"The ingestion engine processes 6 synthetic Markdown knowledge-base documents covering vehicle architectures, communication matrices, and threat/mitigation libraries. The system performs section-aware recursive chunking, producing 70 structural sections and 209 vector chunks. These are embedded via BAAI/bge-small-en-v1.5 into ChromaDB using unique composite SHA-256 IDs."*

### Stage 3: Architecture & Asset Extraction (1 min)
- **Visual:** Pages `03_Architecture_Analysis.py` and `04_Asset_Analysis.py`.
- **Action:** Click **"Run Architecture Analysis"**.
- **Talking Point:** *"The engine extracts ECUs, connected interfaces, sensors, and trust boundaries, dynamically rendering a Graphviz network topology. For each asset, it identifies Confidentiality, Integrity, Availability, and Authenticity (CIA/A) security properties with source document citations."*

### Stage 4: STRIDE Threat Scenario Generation (1.5 min)
- **Visual:** Page `06_Threat_Analysis.py`.
- **Action:** Click **"Generate Threats"**.
- **Talking Point:** *"Candidate threat scenarios are synthesized under the STRIDE framework. Each threat includes target asset associations, attack surfaces, preconditions, and evidence expanders linking back to the source text chunks."*

### Stage 5: Deterministic Risk Assessment & Guardrails (1.5 min)
- **Visual:** Page `07_Risk_Assessment.py`.
- **Action:** Display the Plotly Risk Matrix Heatmap.
- **Talking Point:** *"To eliminate arithmetic hallucinations, risk calculation uses deterministic Python arithmetic: Risk Score = max(Impact) x Feasibility Score. The language model evaluates qualitative ratings, but the numerical score is computed deterministically in code. Furthermore, if AI output parsing fails, the system does not silently assign a low score; it explicitly flags the item as 'Unresolved (Parsing Error)' for manual engineer review."*

### Stage 6: Mitigations, Requirements, & Traceability (1 min)
- **Visual:** Pages `08_Mitigations.py` and `09_TARA_Report.py`.
- **Talking Point:** *"Defensive controls such as AUTOSAR SecOC, UDS Seed-Key authentication, and hardware HSMs are mapped to threats. Candidate requirements are tagged with mandatory engineer approval notes and can be exported as full Markdown or HTML reports."*

### Stage 7: Empirical Evaluation & Audit Trail (1.5 min)
- **Visual:** Pages `11_Evaluation.py` and `12_Audit_Review.py`.
- **Talking Point:** *"The automated evaluation suite tests 20 ground-truth domain questions. The system recorded a 100.0% Non-Empty Retrieval Rate (all queries returned at least one context chunk), a 67.33% Combined Concept Presence (expected keywords in response or context), and a measured query latency of 0.03 seconds (arithmetic mean: 0.035s) under DEMO FALLBACK mode. All findings support Accept, Edit, Reject, and Needs Review actions, logged to SQLite for auditability."*

---

## 3. Viva Voce Defense Quick Reference

1. **Why RAG instead of Fine-Tuning?**
   - Fine-tuning bakes static parameters into model weights and cannot cite specific document pages. RAG dynamically retrieves private vehicle specifications, grounds claims in verifiable page/section citations, and requires zero retraining when specifications change.
2. **Why is Arithmetic Deterministic while Ratings are AI-Assisted?**
   - Language models are probabilistic and prone to arithmetic errors. We keep the mathematical calculation ($\text{Score} = \text{Impact} \times \text{Feasibility}$) in pure Python code. The language model suggests qualitative ratings based on context, but if parsing fails, the engine safely flags the finding as unresolved rather than defaulting to low risk.
3. **What do the Evaluation Metrics Measure?**
   - Non-Empty Retrieval Rate (100%) confirms that the vector store retrieved chunks for all benchmark queries; it does not measure answer accuracy.
   - Combined Concept Presence (67.33%) checks whether expected benchmark terms appeared in the response or retrieved chunks.
   - The 0.03s latency reflects local ChromaDB query and dictionary lookup under DEMO FALLBACK mode (arithmetic mean across 20 queries: 0.035s, rounded to 0.03s), not external cloud LLM generation time (which is typically 1–3s).
4. **Does this System Claim ISO/SAE 21434 Certification?**
   - No. It is an academic engineering prototype informed by ISO/SAE 21434 and UNECE R155 concepts. All outputs are advisory candidate suggestions requiring qualified cybersecurity engineer review.
