# Model Prompts and Configuration

This directory contains the configuration templates and prompt engineering definitions used by the Automotive Cybersecurity TARA Assistant.

## Directory Contents
- `prompts.py`: Formal system prompts and analysis templates (Asset Identification, Trust Boundaries, Attack Surface, STRIDE Threat Generation, Risk Assessment, Mitigations, and Extractive Q&A).
- `config.py`: Application settings and environment schema (Pydantic-based configuration).
- `.env.example`: Environment variable template for LLM provider setup, local Chroma DB, and retrieval hyperparameters.

## Provider Options
- **Gemini**: `gemini-3.8-flash` via official `google-genai` SDK.
- **Local LLM**: Ollama (`llama3.1:8b`).
- **OpenAI**: `gpt-4o-mini`.
- **Demo Fallback**: Zero-API deterministic offline fallback.
