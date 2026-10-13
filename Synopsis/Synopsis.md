# Project Synopsis: Automotive Cybersecurity TARA Assistant

## Project Overview
The **Automotive Cybersecurity TARA Assistant** is an AI-assisted Threat Analysis and Risk Assessment (TARA) platform designed to support automotive systems and security engineers in aligning with ISO/SAE 21434:2021 and UNECE R155 principles.

## Core Capabilities
1. **Document Ingestion & RAG Pipeline**: Ingests vehicle architectures, communication matrices, and threat libraries using PyMuPDF and ChromaDB vector search.
2. **Extractive Demo Fallback**: Operates reliably under API quota constraints using deterministic, citation-backed extractive QA and predefined cybersecurity datasets.
3. **Automotive Security Analysis**:
   - System & Asset Identification (CGW, TCU, ADAS, IVI, CAN-FD, Automotive Ethernet)
   - Trust Boundary & Attack Surface Characterization
   - STRIDE Threat Scenario Generation & Evidence Grounding
   - Deterministic 2D Risk Scoring (Safety, Financial, Operational, Privacy vs. Attack Feasibility)
   - Defensive Mitigation Recommendations & Traceability Matrix Construction
4. **Engineering Review & Responsible AI Controls**: Strict review status tracking (`needs_review`, `accepted`, `edited`, `rejected`) and audit event logging.
