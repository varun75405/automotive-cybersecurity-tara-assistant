import sys
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.models.schemas import MitigationItem

logger = logging.getLogger(__name__)

def _extract_json_object(text: str) -> dict:
    """Helper to safely extract JSON object from LLM output."""
    text = text.strip()
    if "[DEMO FALLBACK MODE]" in text:
        text = text.replace("[DEMO FALLBACK MODE]", "").strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    start_obj = text.find('{')
    if start_obj != -1:
        end_obj = text.rfind('}')
        if end_obj != -1:
            try:
                parsed = json.loads(text[start_obj:end_obj+1])
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    return {}

def _evaluate_threat_specific_candidate(threat_text: str, surface_text: str) -> dict:
    """Return domain-specific candidate controls matched to the actual threatened security property."""
    t_low = f"{threat_text} {surface_text}".lower()
    
    # 1. Passive Eavesdropping (Confidentiality) -> Note: MAC/SecOC does NOT provide encryption
    if "eavesdrop" in t_low or "sniff" in t_low:
        return {
            "control": "Payload Encryption & Bus Access Segmentation",
            "category": "secure_communication",
            "description": (
                "Candidate recommendation: Evaluate higher-layer payload encryption for sensitive parameters, "
                "bus access isolation, and gateway firewalling. Note: Message Authentication Codes (AUTOSAR SecOC) "
                "verify authenticity/integrity but do not provide confidentiality against passive eavesdropping. "
                "(engineering review required, not an automatic compliance claim)."
            )
        }
    # 2. Replay Attacks (Freshness / Anti-Replay) -> Requires freshness counters/timestamps, not just static MAC
    elif "replay" in t_low:
        return {
            "control": "Cryptographic Freshness Verification & Anti-Replay Protection",
            "category": "message_integrity",
            "description": (
                "Candidate recommendation: Evaluate monotonic freshness counters, rolling codes, synchronized timestamps, "
                "and freshness value management (AUTOSAR SecOC Freshness Value Manager - FVM) to detect and reject retransmitted frames "
                "(engineering review required, not an automatic compliance claim)."
            )
        }
    # 3. GPS / GNSS Spoofing -> Requires multi-constellation, signal plausibility, sensor cross-checking
    elif "gps" in t_low or "gnss" in t_low or "meaconing" in t_low:
        return {
            "control": "Multi-Constellation Validation & Navigation Plausibility Checks",
            "category": "monitoring",
            "description": (
                "Candidate recommendation: Evaluate multi-constellation GNSS receivers (GPS/Galileo/GLONASS), signal-to-noise ratio plausibility checks, "
                "inertial measurement unit (IMU) dead reckoning cross-validation, and spoofing detection algorithms. "
                "Note: SecOC cannot authenticate physical unencrypted RF satellite signals. "
                "(engineering review required, not an automatic compliance claim)."
            )
        }
    # 4. Sensor Data Manipulation (Camera, Radar, LiDAR) -> Sensor fusion and plausibility checks
    elif "sensor" in t_low or "radar" in t_low or "lidar" in t_low or "camera" in t_low:
        return {
            "control": "Multi-Sensor Fusion & Physical Plausibility Validation",
            "category": "monitoring",
            "description": (
                "Candidate recommendation: Evaluate multi-sensor fusion (cross-validating radar, camera, and LiDAR spatial data), "
                "temporal tracking consistency, optical flow verification, and anomalous signal rejection in ADAS perception pipelines "
                "(engineering review required, not an automatic compliance claim)."
            )
        }
    # 5. Ethernet Interception / MITM -> MACsec (802.1AE), TLS, or SOME/IP-SD authorization
    elif "ethernet" in t_low or "mitm" in t_low:
        return {
            "control": "Automotive Ethernet MACsec (IEEE 802.1AE) & TLS 1.3",
            "category": "secure_communication",
            "description": (
                "Candidate recommendation: Evaluate IEEE 802.1AE MACsec for link-layer point-to-point Ethernet encryption/integrity, "
                "TLS 1.3 for service-oriented SOME/IP-TP communication, and static VLAN domain segmentation on Central Gateway switches "
                "(engineering review required, not an automatic compliance claim)."
            )
        }
    # 6. CAN / CAN-FD message injection & spoofing
    elif any(k in t_low for k in ["can", "injection", "bus", "spoof"]):
        return {
            "control": "AUTOSAR SecOC & Gateway Network Segmentation",
            "category": "message_integrity",
            "description": (
                "Candidate recommendation: Evaluate AUTOSAR SecOC cryptographic message authentication (AES-CMAC), "
                "freshness counters / replay protection, and Central Gateway network segmentation to isolate "
                "CAN-FD clusters (engineering review required, not an automatic compliance claim)."
            )
        }
    # 7. OTA firmware update compromise
    elif any(k in t_low for k in ["ota", "firmware", "update"]):
        return {
            "control": "Asymmetric Firmware Verification & Secure Boot",
            "category": "secure_ota",
            "description": (
                "Candidate recommendation: Evaluate cryptographically signed firmware verification (ECDSA/RSA-3072), "
                "hardware-anchored Secure Boot (HSM/SHE), update authenticity and integrity validation, rollback protection "
                "monotonic counters, and backend signing-key protection (engineering review required, not an automatic compliance claim)."
            )
        }
    # 8. UDS diagnostic access
    elif any(k in t_low for k in ["diagnostic", "uds", "obd", "0x27", "flashing"]):
        return {
            "control": "UDS SecurityAccess Authentication & Diagnostic Rate Limiting",
            "category": "secure_diagnostics",
            "description": (
                "Candidate recommendation: Evaluate ISO 14229 UDS SecurityAccess (0x27) challenge-response or certificate "
                "authentication (0x29), diagnostic-session authorization (0x10), anti-brute-force rate limiting, and secure "
                "programming restrictions (engineering review required, not an automatic compliance claim)."
            )
        }
    # 9. Hardware key extraction
    elif "key" in t_low or "hsm" in t_low or "hardware" in t_low:
        return {
            "control": "Hardware Security Module (HSM) Key Protection & Tamper Resistance",
            "category": "access_control",
            "description": (
                "Candidate recommendation: Evaluate EVITA-compliant Hardware Security Module (HSM) cryptographic isolation, "
                "permanently disabled JTAG/debug ports in production fuses, side-channel attack mitigations, and secure key generation "
                "(engineering review required, not an automatic compliance claim)."
            )
        }
    return {
        "control": "Cryptographic Authentication & Interface Access Controls",
        "category": "access_control",
        "description": (
            "Candidate recommendation: Evaluate interface access control, cryptographic verification, and domain boundary "
            "filtering (engineering review required, not an automatic compliance claim)."
        )
    }

def recommend_mitigations(threats, risks, retriever, llm_client) -> list[MitigationItem]:
    mitigations = []
    try:
        categories = ['access_control', 'authentication', 'message_integrity', 'secure_communication', 'secure_diagnostics', 'secure_boot', 'secure_ota', 'network_segmentation', 'monitoring', 'logging', 'rate_limiting']
        
        for i, threat in enumerate(threats):
            # Strictly validate threat: do not generate mitigations for invalid or excluded threats
            if not getattr(threat, "is_valid", lambda: True)():
                logger.warning(f"Skipping mitigation recommendation for invalid/incomplete threat candidate: {threat.threat_id}")
                continue

            # Target initial context queries for mitigation generation
            context_queries = ['mitigation library', threat.threat]
            all_citations = []
            for q in context_queries:
                all_citations.extend(retriever.retrieve(q, top_k=2))
            
            seen = set()
            unique_citations = []
            for c in all_citations:
                cid = f"{c.document_name}-{c.chunk_text[:30]}"
                if cid not in seen:
                    seen.add(cid)
                    unique_citations.append(c)

            context = "\n".join([f"Doc: {c.document_name}\nText: {c.chunk_text}" for c in unique_citations])
            
            prompt = f"""
Recommend a threat-specific defensive mitigation control for the following automotive threat based on the context.
Threat: {threat.threat}
Target Asset: {threat.asset}
Attack Surface: {threat.attack_surface}
Description: {threat.threat_description}
Allowed Categories: {', '.join(categories)}

Specialized Guidance:
- For CAN/CAN-FD message injection: evaluate message authentication (SecOC, CMAC), freshness/replay protection, and network segmentation.
- For OTA firmware compromise: evaluate signed firmware verification, secure boot, update authenticity/integrity, rollback protection, and backend signing-key protection.
- For Unauthorized UDS diagnostics: evaluate SecurityAccess/Authentication controls, diagnostic-session authorization, rate limiting, and secure programming restrictions.

Note: Recommendations are candidate controls requiring engineering review, not automatic compliance claims.

Provide JSON with:
- recommended_control
- control_category
- description

Context:
{context}
"""
            response = llm_client.generate(prompt=prompt, system_prompt="You are a TARA mitigation recommender. Output strictly JSON.")
            parsed = _extract_json_object(response)

            fallback = _evaluate_threat_specific_candidate(threat.threat, threat.attack_surface)
            # Determine if fallback matched a SPECIFIC domain pattern (not the catch-all generic)
            generic_controls = {
                "Cryptographic Authentication & Boundary Filtering",
                "cryptographic authentication & boundary filtering"
            }
            fallback_is_specific = fallback["control"].lower() not in generic_controls

            # Prefer the domain-specific engineered fallback when it matched a known threat pattern,
            # since LLM in demo mode can return a generic "else" response for niche threats.
            if fallback_is_specific:
                rec_control = fallback["control"]
                cat = fallback["category"]
                raw_desc = fallback["description"]
            else:
                rec_control = str(parsed.get("recommended_control", "")).strip() or fallback["control"]
                cat = parsed.get("control_category", "").strip() or fallback["category"]
                if cat not in categories:
                    cat = fallback["category"]
                raw_desc = str(parsed.get("description", "")).strip() or fallback["description"]

            if "engineering review" not in raw_desc.lower():
                raw_desc += " (Candidate recommendation requiring engineering review, not an automatic compliance claim.)"

            # Query knowledge base specifically for evidence supporting the recommended defensive control
            control_queries = [rec_control, f"{rec_control} {cat}"]
            rc_lower = rec_control.lower()
            t_lower = threat.threat.lower()
            if any(k in rc_lower or k in t_lower for k in ["secoc", "can", "injection"]):
                control_queries.extend([
                    "AUTOSAR SecOC message authentication",
                    "Message Authentication MAC CMAC SecOC",
                    "Network Segmentation Gateway Filtering"
                ])
            elif any(k in rc_lower or k in t_lower for k in ["firmware", "ota", "boot"]):
                control_queries.extend([
                    "Secure Boot Verified Boot Chain",
                    "Secure OTA Signed Firmware Rollback Protection"
                ])
            elif any(k in rc_lower or k in t_lower for k in ["diagnostic", "uds", "0x27"]):
                control_queries.extend([
                    "Secure Diagnostics Seed-Key Certificate Auth 0x27",
                    "Rate Limiting Gateway Brute-force"
                ])

            control_citations = []
            seen_c = set()
            for cq in control_queries:
                found = retriever.retrieve(cq, top_k=2)
                for c in found:
                    cid = f"{c.document_name}-{c.chunk_text[:30]}"
                    if cid not in seen_c:
                        seen_c.add(cid)
                        control_citations.append(c)

            if control_citations:
                evidence = control_citations
                confidence = "Medium"
            else:
                evidence = []
                confidence = "Low (Hypothesis)"
                missing_note = f"[Hypothesis - Candidate control '{rec_control}' lacks supporting knowledge-base citations]"
                if missing_note not in raw_desc:
                    raw_desc = f"{raw_desc} {missing_note}".strip()
                
            mitigations.append(MitigationItem(
                mitigation_id=f"MIT-{threat.threat_id.split('-')[-1]}",
                threat_id=threat.threat_id,
                asset=threat.asset,
                threat=threat.threat,
                recommended_control=rec_control,
                control_category=cat,
                description=raw_desc,
                evidence=evidence,
                confidence=confidence,
                review_status="needs_review"
            ))
    except Exception as e:
        logger.error(f"Error in recommend_mitigations: {e}")

    return mitigations
