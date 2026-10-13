import sys
import os
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, settings=None):
        if settings is None:
            try:
                from config import get_settings
                self.settings = get_settings()
            except ImportError:
                class DummySettings:
                    llm_provider = 'demo'
                    openai_api_key = ''
                    openai_api_base = None
                    openai_model = 'gpt-3.5-turbo'
                    local_llm_url = 'http://localhost:8000'
                    local_llm_model = 'local-model'
                self.settings = DummySettings()
        else:
            self.settings = settings
            
        self.provider = getattr(self.settings, 'llm_provider', 'demo')
        self.last_fallback_reason: str = ""
        self.used_fallback_this_run: bool = False

    @property
    def is_fallback_active(self) -> bool:
        return bool(self.used_fallback_this_run or self.last_fallback_reason)

    @property
    def mode(self) -> str:
        if self.provider == 'demo':
            return 'DEMO FALLBACK'
        elif self.provider == 'gemini':
            model = getattr(self.settings, 'gemini_model', 'gemini-3.8-flash')
            if self.is_fallback_active:
                return f"DEMO FALLBACK (Predefined Data — Gemini Fallback: {self.last_fallback_reason or 'Quota/Unavailable'})"
            return f"REAL LLM (Gemini: {model})"
        elif self.provider == 'local':
            model = getattr(self.settings, 'local_llm_model', 'local-model')
            return f"REAL LLM (Ollama: {model})"
        elif self.provider == 'openai':
            model = getattr(self.settings, 'openai_model', 'openai-model')
            return f"REAL LLM (OpenAI: {model})"
        return 'REAL LLM'

    @property
    def model_name(self) -> str:
        if self.provider == 'gemini':
            return getattr(self.settings, 'gemini_model', 'gemini-3.8-flash')
        elif self.provider == 'local':
            return getattr(self.settings, 'local_llm_model', 'llama3.1:8b')
        elif self.provider == 'openai':
            return getattr(self.settings, 'openai_model', 'gpt-4o-mini')
        return 'demo-fallback'

    @property
    def is_demo(self) -> bool:
        return self.provider == 'demo'

    def generate(self, prompt: str, system_prompt: str = None) -> str:
        if self.is_demo:
            return self._demo_generate(prompt)

        # ── Gemini Provider (Official google-genai SDK) ─────────────────────
        if self.provider == 'gemini':
            api_key = getattr(self.settings, 'gemini_api_key', '') or os.getenv('GEMINI_API_KEY', '')
            if not api_key:
                err_msg = (
                    "GEMINI_API_KEY is not configured. Please set GEMINI_API_KEY in your .env file "
                    "or environment variables to enable Google Gemini analysis."
                )
                logger.error(err_msg)
                return f"[LIVE LLM CALL FAILED: {err_msg}]"

            try:
                from google import genai
                from google.genai import types

                model = getattr(self.settings, 'gemini_model', 'gemini-3.8-flash')
                client = genai.Client(api_key=api_key)

                # Request JSON output if prompt indicates structured output
                lower_p = prompt.lower()
                is_json_requested = "json" in lower_p or "return a json" in lower_p or "output strictly a json" in (system_prompt or "").lower()

                config_kwargs = {}
                if system_prompt:
                    config_kwargs["system_instruction"] = system_prompt
                if is_json_requested:
                    config_kwargs["response_mime_type"] = "application/json"
                config_kwargs["temperature"] = 0.2

                config = types.GenerateContentConfig(**config_kwargs)

                # Attempt call with bounded retry for transient 503 high demand
                max_retries = 2
                response = None
                for attempt in range(max_retries + 1):
                    try:
                        response = client.models.generate_content(
                            model=model,
                            contents=prompt,
                            config=config
                        )
                        break
                    except Exception as call_err:
                        err_str = str(call_err)
                        if "503" in err_str and attempt < max_retries:
                            import time
                            time.sleep(2.0)
                            continue
                        raise call_err

                if response and response.text:
                    return response.text
                return "[]" if is_json_requested else ""

            except Exception as e:
                err_desc = str(e)
                # Ensure API key is never leaked in logs or error messages
                if api_key and api_key in err_desc:
                    err_desc = err_desc.replace(api_key, "[REDACTED_GEMINI_KEY]")

                is_quota_429 = "429" in err_desc or "RESOURCE_EXHAUSTED" in err_desc or "quota" in err_desc.lower()
                is_503_unavailable = "503" in err_desc or "UNAVAILABLE" in err_desc

                if is_quota_429 or is_503_unavailable:
                    reason = "HTTP 429 Quota Exhausted" if is_quota_429 else "HTTP 503 Unavailable (Retries Exhausted)"
                    self.last_fallback_reason = reason
                    self.used_fallback_this_run = True
                    logger.warning(
                        f"Gemini API returned {reason}. Falling back to deterministic DEMO MODE predefined automotive data."
                    )
                    return self._demo_generate(prompt)

                logger.error(f"Gemini API call failed: {err_desc}")
                return f"[LIVE LLM CALL FAILED: {err_desc}]"

        # ── OpenAI & Local (Ollama) Providers ───────────────────────────────
        try:
            import openai

            if self.provider == 'openai':
                client = openai.OpenAI(
                    api_key=self.settings.openai_api_key,
                    base_url=self.settings.openai_api_base
                )
                model = self.settings.openai_model
            elif self.provider == 'local':
                client = openai.OpenAI(
                    api_key='not-needed',
                    base_url=self.settings.local_llm_url
                )
                model = self.settings.local_llm_model
            else:
                return "[DEMO FALLBACK MODE] Unknown provider, using demo fallback."

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=model,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Live LLM generation failed ({e}); falling back to demo response.")
            # Gracefully fall back to demo response if live model call fails
            fallback_resp = self._demo_generate(prompt)
            return f"[LIVE LLM CALL FAILED: {str(e)}]\n\n{fallback_resp}"

    def _demo_generate(self, prompt: str) -> str:
        lower_prompt = prompt.lower()

        # 1. Asset identification prompt
        if "identify all automotive assets" in lower_prompt or ("asset_id" in lower_prompt and "asset_type" in lower_prompt):
            assets_payload = [
                {
                    "asset_id": "ASSET-001",
                    "name": "Central Gateway (CGW)",
                    "asset_type": "ECU",
                    "description": "Central communication gateway routing messages between CAN-FD and Automotive Ethernet domains",
                    "related_ecu": ["ADAS ECU", "Telematics Control Unit (TCU)", "Body Control Module (BCM)"],
                    "related_interface": ["CAN-FD", "Automotive Ethernet", "OBD-II"],
                    "security_properties": ["Integrity", "Authenticity", "Availability"]
                },
                {
                    "asset_id": "ASSET-002",
                    "name": "Telematics Control Unit (TCU)",
                    "asset_type": "ECU",
                    "description": "Connects vehicle to cellular networks and remote cloud backends for telemetry and OTA updates",
                    "related_ecu": ["Central Gateway (CGW)"],
                    "related_interface": ["Cellular 4G/5G", "Automotive Ethernet"],
                    "security_properties": ["Confidentiality", "Integrity", "Authenticity"]
                },
                {
                    "asset_id": "ASSET-003",
                    "name": "In-Vehicle CAN-FD Bus",
                    "asset_type": "Interface / Bus",
                    "description": "High-speed powertrain and chassis real-time control network",
                    "related_ecu": ["Central Gateway (CGW)", "Powertrain ECU", "ADAS ECU"],
                    "related_interface": ["CAN-FD"],
                    "security_properties": ["Integrity", "Authenticity", "Availability"]
                }
            ]
            return json.dumps(assets_payload, indent=2)

        # 2. Trust boundaries prompt
        elif "identify all trust boundaries" in lower_prompt or ("boundary_id" in lower_prompt and "connected_components" in lower_prompt):
            boundaries_payload = [
                {
                    "boundary_id": "TB-001",
                    "name": "External Wireless Boundary",
                    "connected_components": ["Telematics Control Unit (TCU)", "Cellular Network", "Cloud Backend"],
                    "rationale": "Separates public wireless communications from internal vehicle networks"
                },
                {
                    "boundary_id": "TB-002",
                    "name": "Gateway Domain Boundary",
                    "connected_components": ["Central Gateway (CGW)", "CAN-FD Bus", "Automotive Ethernet"],
                    "rationale": "Enforces firewall filtering and domain isolation between infotainment and safety-critical control domains"
                }
            ]
            return json.dumps(boundaries_payload, indent=2)

        # 3. Attack surface prompt
        elif "identify all attack surfaces" in lower_prompt or ("surface_id" in lower_prompt and "exposure" in lower_prompt):
            surfaces_payload = [
                {
                    "surface_id": "AS-001",
                    "interface": "OBD-II Diagnostic Port",
                    "connected_component": "Central Gateway (CGW)",
                    "exposure": "Physical Interior Cabin",
                    "security_concern": "Unauthorized UDS diagnostic request injection and firmware tampering"
                },
                {
                    "surface_id": "AS-002",
                    "interface": "Cellular Telematics Interface",
                    "connected_component": "Telematics Control Unit (TCU)",
                    "exposure": "Remote Wireless",
                    "security_concern": "Remote command execution, compromised OTA update path, and backend spoofing"
                },
                {
                    "surface_id": "AS-003",
                    "interface": "In-Vehicle CAN-FD Bus",
                    "connected_component": "Powertrain & ADAS ECUs",
                    "exposure": "Internal In-Vehicle Network",
                    "security_concern": "Arbitrary message injection, frame spoofing, and bus-off denial of service"
                }
            ]
            return json.dumps(surfaces_payload, indent=2)

        # 4. Threat generation prompt
        elif "generate candidate threats" in lower_prompt or ("threat_description" in lower_prompt and "potential_impact" in lower_prompt):
            threats_payload = [
                {
                    "asset": "Central Gateway (CGW)",
                    "attack_surface": "In-Vehicle CAN-FD Bus",
                    "threat": "Unauthorized CAN Message Injection",
                    "threat_description": "Adversary injects spoofed actuator commands over CAN-FD leading to unintended vehicle dynamics",
                    "potential_impact": "Unintended acceleration, braking, or steering causing severe safety hazard",
                    "preconditions": ["Access to in-vehicle CAN bus via compromised ECU or physical tap"]
                },
                {
                    "asset": "Telematics Control Unit (TCU)",
                    "attack_surface": "Cellular Telematics Interface",
                    "threat": "Compromised OTA Firmware Path",
                    "threat_description": "Adversary manipulates remote firmware update packages in transit to execute arbitrary malicious code",
                    "potential_impact": "Persistent remote compromise of vehicle telematics and control gateway",
                    "preconditions": ["Compromised backend signing credentials or cellular man-in-the-middle"]
                },
                {
                    "asset": "Central Gateway (CGW)",
                    "attack_surface": "OBD-II Diagnostic Port",
                    "threat": "Unauthorized Diagnostic Access",
                    "threat_description": "Adversary bypasses UDS Security Access service (0x27) to flash unauthorized calibration data",
                    "potential_impact": "ECU parameter tampering or vehicle theft",
                    "preconditions": ["Physical connection to OBD-II port inside vehicle cabin"]
                }
            ]
            return json.dumps(threats_payload, indent=2)

        # 5. Risk qualitative assessment prompt
        elif "qualitative assessment" in lower_prompt or ("safety (1-4)" in lower_prompt and "feasibility" in lower_prompt):
            # Isolate threat focus from the prompt using the last 'threat:' occurrence
            threat_focus = lower_prompt
            if "threat:" in lower_prompt:
                threat_focus = lower_prompt.split("threat:")[-1].split("description:")[0].strip()

            if any(k in threat_focus for k in ["ota", "firmware", "update"]):
                risk_payload = {
                    "safety": 4,
                    "financial": 4,
                    "privacy": 3,
                    "availability": 4,
                    "rationale": "Fleet-wide impact across safety, financial recall, and vehicle availability (S:4, F:4, A:4). However, attack feasibility is Low due to requiring compromise of OEM cloud signing infrastructure or hardware root of trust.",
                    "feasibility": "Low"
                }
            elif any(k in threat_focus for k in ["diagnostic", "uds", "obd", "0x27"]):
                risk_payload = {
                    "safety": 2,
                    "financial": 3,
                    "privacy": 2,
                    "availability": 2,
                    "rationale": "High attack feasibility via standard physical OBD-II diagnostic connector in cabin with off-the-shelf scan tools (Feasibility: High). Safety impact is bounded as diagnostic routines require vehicle-stationary preconditions, but tampering causes significant financial/calibration impact (F:3, S:2).",
                    "feasibility": "High"
                }
            elif any(k in threat_focus for k in ["can", "injection", "bus", "spoofing"]):
                risk_payload = {
                    "safety": 4,
                    "financial": 3,
                    "privacy": 1,
                    "availability": 3,
                    "rationale": "Safety-critical control manipulation of steering/braking poses life-threatening hazard (S:4); substantial financial recall damage (F:3). Attack feasibility is Medium due to requiring internal in-vehicle network bus access.",
                    "feasibility": "Medium"
                }
            else:
                risk_payload = {
                    "safety": 2,
                    "financial": 2,
                    "privacy": 2,
                    "availability": 2,
                    "rationale": "Moderate operational impact across vehicle subsystems; attack feasibility is Medium.",
                    "feasibility": "Medium"
                }
            return json.dumps(risk_payload, indent=2)

        # 6. Mitigation recommendation prompt
        elif "recommend a mitigation control" in lower_prompt or ("recommended_control" in lower_prompt and "control_category" in lower_prompt):
            # Isolate the specific threat / description lines before the allowed categories and guidance sections
            threat_focus = lower_prompt
            if "threat:" in lower_prompt:
                threat_focus = lower_prompt.split("threat:")[-1].split("allowed categories:")[0].strip()

            if any(k in threat_focus for k in ["can", "injection", "bus", "spoofing"]):
                mitigation_payload = {
                    "recommended_control": "AUTOSAR SecOC & Gateway Network Segmentation",
                    "control_category": "message_integrity",
                    "description": "Candidate recommendation: Evaluate AUTOSAR SecOC cryptographic message authentication (AES-CMAC), freshness counters / replay protection, and Central Gateway network segmentation to isolate CAN-FD clusters (engineering review required, not an automatic compliance claim)."
                }
            elif any(k in threat_focus for k in ["ota", "firmware", "update"]):
                mitigation_payload = {
                    "recommended_control": "Asymmetric Firmware Verification & Secure Boot",
                    "control_category": "secure_ota",
                    "description": "Candidate recommendation: Evaluate cryptographically signed firmware verification (ECDSA/RSA-3072), hardware-anchored Secure Boot (HSM/SHE), update authenticity and integrity validation, rollback protection monotonic counters, and backend signing-key protection (engineering review required, not an automatic compliance claim)."
                }
            elif any(k in threat_focus for k in ["diagnostic", "uds", "obd", "0x27"]):
                mitigation_payload = {
                    "recommended_control": "UDS SecurityAccess & Diagnostic Rate Limiting",
                    "control_category": "secure_diagnostics",
                    "description": "Candidate recommendation: Evaluate ISO 14229 UDS SecurityAccess (0x27) challenge-response or certificate authentication (0x29), diagnostic-session authorization (0x10), anti-brute-force rate limiting, and secure programming restrictions (engineering review required, not an automatic compliance claim)."
                }
            else:
                mitigation_payload = {
                    "recommended_control": "Cryptographic Authentication & Boundary Filtering",
                    "control_category": "access_control",
                    "description": "Candidate recommendation: Evaluate interface access control, cryptographic verification, and domain boundary filtering (engineering review required, not an automatic compliance claim)."
                }
            return json.dumps(mitigation_payload, indent=2)

        # 7. Requirement generation prompt
        elif "candidate cybersecurity requirement" in lower_prompt or ("requirement_text" in lower_prompt and "rationale" in lower_prompt):
            req_payload = {
                "requirement_text": "The Gateway ECU and connected safety ECUs shall authenticate all safety-critical CAN-FD messages using AUTOSAR SecOC with a 64-bit truncated MAC and freshness counter.",
                "rationale": "Mitigates unauthorized message injection by rejecting frames without valid cryptographic authentication."
            }
            return json.dumps(req_payload, indent=2)

        # 8. General Q&A / Evaluation prompt — extractive answer from embedded context
        else:
            return self._extractive_qa_fallback(prompt)

    def _extractive_qa_fallback(self, prompt: str) -> str:
        """Parse the context embedded in the Q&A prompt and synthesise a factual extractive answer.

        The prompt from get_qa_prompt() has this structure::

            Answer the user query based on the following context.
            ...
            Context:
            ['chunk1 text', 'chunk2 text', ...]

            Query: user question
            ...

        We extract the context list literal and the query, then search context sentences
        for keywords from the query and return the most relevant sentences verbatim.
        We NEVER invent facts; if nothing relevant is found we say so explicitly.
        """
        import re

        # ── Extract the query ────────────────────────────────────────────────
        query_match = re.search(r'\nQuery:\s*(.+?)(?:\n|$)', prompt, re.IGNORECASE | re.DOTALL)
        query_text = query_match.group(1).strip() if query_match else ""

        # ── Extract the context section ──────────────────────────────────────
        ctx_match = re.search(r'\nContext:\n(.*?)(?:\nQuery:|\nIf evidence|$)', prompt, re.IGNORECASE | re.DOTALL)
        raw_context = ctx_match.group(1).strip() if ctx_match else ""

        # Decode Python list representation produced by get_qa_prompt()
        context_sentences: list[str] = []
        if raw_context.startswith('[') and raw_context.endswith(']'):
            # It's a Python list literal — parse individual string items
            try:
                import ast
                chunks: list = ast.literal_eval(raw_context)
                for chunk in chunks:
                    if isinstance(chunk, str):
                        # Split into sentences for finer granularity
                        for sent in re.split(r'(?<=[.!?])\s+', chunk):
                            s = sent.strip()
                            if len(s) > 20:
                                context_sentences.append(s)
            except Exception:
                # Fallback: treat whole block as one big text
                for sent in re.split(r'(?<=[.!?])\s+', raw_context):
                    s = sent.strip()
                    if len(s) > 20:
                        context_sentences.append(s)
        else:
            # Plain text context
            for sent in re.split(r'(?<=[.!?])\s+', raw_context):
                s = sent.strip()
                if len(s) > 20:
                    context_sentences.append(s)

        if not context_sentences:
            return (
                "[DEMO FALLBACK — EXTRACTIVE ANSWER] "
                "No relevant context was retrieved from the knowledge base for this query. "
                f"Unable to answer: '{query_text}'. "
                "Please upload relevant documents and re-index before querying."
            )

        # ── Score sentences by keyword overlap with query ────────────────────
        query_words = set(re.findall(r'\b\w{3,}\b', query_text.lower()))
        # Remove common stop words that add no discriminative power
        stop_words = {'the', 'and', 'for', 'are', 'was', 'what', 'how', 'does', 'each', 'does',
                      'which', 'this', 'that', 'with', 'from', 'its', 'who', 'does', 'according'}
        query_words -= stop_words

        scored: list[tuple[float, str]] = []
        for sent in context_sentences:
            sent_lower = sent.lower()
            sent_words = set(re.findall(r'\b\w{3,}\b', sent_lower))
            if not query_words:
                scored.append((0.0, sent))
                continue
            overlap = len(query_words & sent_words) / len(query_words)
            scored.append((overlap, sent))

        scored.sort(key=lambda x: x[0], reverse=True)

        # Select up to 5 unique sentences that have ANY keyword overlap
        # (score > 0.0) with the query. This avoids the strict 0.2 threshold
        # that dropped valid low-overlap facts, while still filtering out
        # completely unrelated sentences (score == 0.0).
        # Exact-duplicate sentences are dropped via the seen_sents set.
        top_sentences: list[str] = []
        seen_sents: set[str] = set()
        for _score, s in scored:
            if _score <= 0.0:
                continue  # skip zero-overlap sentences
            if s not in seen_sents:
                seen_sents.add(s)
                top_sentences.append(s)
            if len(top_sentences) >= 5:
                break

        if not top_sentences:
            # No relevant context found — return a truthful "not found" message
            return (
                "[DEMO FALLBACK — EXTRACTIVE ANSWER] "
                "The retrieved knowledge-base excerpts do not contain information directly relevant to: "
                f"'{query_text}'. "
                "The available documents cover vehicle E/E architecture, threat analysis, and mitigation controls. "
                "For document-specific questions, ensure the relevant PDF is uploaded and indexed."
            )

        # ── Build answer from top matching sentences ─────────────────────────
        answer_body = " ".join(top_sentences)
        return (
            f"[DEMO FALLBACK — EXTRACTIVE ANSWER]\n\n"
            f"Based on the retrieved knowledge-base excerpts:\n\n"
            f"{answer_body}\n\n"
            f"*(Source: retrieved document chunks — Demo fallback mode; no live LLM was called. "
            f"For authoritative answers, configure a live Gemini API key.)*"
        )
