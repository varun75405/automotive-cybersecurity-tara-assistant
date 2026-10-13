import sys
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.models.schemas import ThreatItem

logger = logging.getLogger(__name__)

def _extract_json_array(text: str) -> list:
    """Helper to safely extract JSON list from LLM output."""
    text = text.strip()
    if text.startswith("[LIVE LLM CALL FAILED:"):
        end_bracket = text.find("]")
        error_msg = text[len("[LIVE LLM CALL FAILED:"):end_bracket].strip() if end_bracket != -1 else "unknown error"
        raise RuntimeError(f"LLM call failed: {error_msg}")
    if "[DEMO FALLBACK MODE]" in text:
        text = text.replace("[DEMO FALLBACK MODE]", "").strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    start_arr = text.find('[')
    if start_arr != -1:
        end_arr = text.rfind(']')
        if end_arr != -1:
            try:
                parsed = json.loads(text[start_arr:end_arr+1])
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
        elif isinstance(parsed, dict) and "threats" in parsed and isinstance(parsed["threats"], list):
            return parsed["threats"]
    except Exception:
        pass
    return []

def _build_rejected_item(i: int, item: dict, reason: str) -> ThreatItem:
    """Build a ThreatItem that records why a candidate was rejected."""
    return ThreatItem(
        threat_id=f"REJECTED-{i:03d}",
        asset=str(item.get("asset") or "").strip(),
        attack_surface=str(item.get("attack_surface") or "").strip(),
        threat=str(item.get("threat") or "[invalid]").strip(),
        threat_description=str(item.get("threat_description") or "").strip(),
        potential_impact=str(item.get("potential_impact") or "").strip(),
        preconditions=str(item.get("preconditions") or "").strip(),
        evidence=[],
        confidence="Rejected (Invalid Candidate)",
        review_status="rejected",
        rejection_reason=reason,
    )


def generate_threats_with_rejects(
    retriever, llm_client, assets, attack_surfaces, max_candidates: int = 5
) -> tuple[list[ThreatItem], list[ThreatItem]]:
    """Generate threat candidates and return (valid_threats, rejected_threats).

    valid_threats: passed is_valid() and are suitable for downstream pipeline.
    rejected_threats: failed structural validation; each has rejection_reason set.
    Hypothesis candidates (no evidence) remain in valid_threats with
    confidence='Low (Hypothesis)' for explicit engineering review.
    
    Note: Generated threats are representative candidate scenarios for qualified
    engineering review and are not an exhaustive automotive threat assessment.
    """
    import time
    t_start = time.time()
    valid_threats: list[ThreatItem] = []
    rejected_threats: list[ThreatItem] = []
    try:
        asset_names = [a.name for a in assets] if assets else []
        surface_names = [s.interface for s in attack_surfaces] if attack_surfaces else []

        t_retr_start = time.time()
        queries = ['threat library', 'automotive vulnerabilities', 'cybersecurity threats'] + asset_names[:2]
        all_citations = []
        for q in queries:
            all_citations.extend(retriever.retrieve(q, top_k=3))

        seen = set()
        unique_citations = []
        for c in all_citations:
            cid = f"{c.document_name}-{c.chunk_text[:20]}"
            if cid not in seen:
                seen.add(cid)
                unique_citations.append(c)

        context = "\n".join([f"Doc: {c.document_name}\nText: {c.chunk_text}" for c in unique_citations])
        t_retr_dur = time.time() - t_retr_start
        logger.info(f"[ThreatAnalysis] Pre-generation retrieval complete: {len(unique_citations)} unique chunks in {t_retr_dur:.2f}s")

        prompt = f"""Generate candidate automotive threat scenarios for the following assets and attack surfaces based on the context.
Assets: {', '.join(asset_names)}
Attack Surfaces: {', '.join(surface_names)}

Scope & Candidate Limit:
- Generate up to {max_candidates} key candidate threat scenarios covering distinct STRIDE categories.
- These are prioritized candidate scenarios for engineering review, not an exhaustive assessment.

Taxonomy Alignment:
- Distinguish CAN Injection vs. CAN Eavesdropping vs. Replay Attacks.
- Distinguish GPS/GNSS Spoofing (targeting navigation/timing antennas) vs. Sensor Data Manipulation (targeting cameras, radar, LiDAR).
- Distinguish Ethernet MITM vs. Unauthorized UDS Diagnostics vs. Compromised OTA Firmware.
- For Hardware Security Module (HSM), only identify threats if physically or cryptographically justified in documentation (e.g. key extraction via side-channel/JTAG). DO NOT create dummy or empty entries.

Return strictly a JSON list of {max_candidates} objects with keys:
- asset (target component or network)
- attack_surface (specific interface — MUST be non-empty, non-null)
- threat (specific threat name — MUST NOT be null, empty, or 'None')
- threat_description (technical mechanism of attack — concise, specific)
- potential_impact (safety, operational, financial, or privacy impact — MUST be specified)
- preconditions (access requirements or required attacker capability)

Context:
{context}
"""
        t_llm_start = time.time()
        response = llm_client.generate(
            prompt=prompt,
            system_prompt="You are an expert automotive cybersecurity TARA analyst. Output strictly a JSON array of objects. Never output None, null, or empty fields."
        )
        t_llm_dur = time.time() - t_llm_start
        logger.info(f"[ThreatAnalysis] LLM threat generation completed in {t_llm_dur:.2f}s (response length: {len(response)} chars)")

        parsed = _extract_json_array(response)

        seen_threat_keys: set = set()
        valid_counter = 0
        reject_counter = 0
        relevance_threshold = getattr(retriever, "relevance_threshold", 0.30)
        t_ground_start = time.time()

        for i, item in enumerate(parsed):
            if isinstance(item, str):
                item = {"threat": item, "threat_description": item}

            threat_title = str(item.get("threat") or "").strip()
            threat_asset = str(item.get("asset") or "").strip()
            threat_surface = str(item.get("attack_surface") or "").strip()
            base_desc = str(item.get("threat_description") or "").strip()
            pot_impact = str(item.get("potential_impact") or "").strip()
            precond = item.get("preconditions", "")
            if isinstance(precond, list):
                precond = "; ".join(str(p) for p in precond if p)
            else:
                precond = str(precond).strip()

            # Fix typos
            threat_asset = threat_asset.replace("Celullar", "Cellular").replace("celullar", "cellular")
            threat_surface = threat_surface.replace("Celullar", "Cellular").replace("celullar", "cellular")

            candidate = ThreatItem(
                threat_id="THREAT-TEMP",
                asset=threat_asset,
                attack_surface=threat_surface,
                threat=threat_title,
                threat_description=base_desc,
                potential_impact=pot_impact,
                preconditions=precond,
                evidence=[],
                confidence="Medium",
                review_status="needs_review",
            )

            # Structural validation — reject malformed candidates
            if not candidate.is_valid():
                reason = candidate.validation_error()
                logger.warning(f"Rejecting malformed candidate threat at index {i}: {reason}")
                reject_counter += 1
                rejected_threats.append(_build_rejected_item(reject_counter, item, reason))
                continue

            # Deduplication
            dedup_key = f"{threat_title.lower()}::{threat_asset.lower()}"
            if dedup_key in seen_threat_keys:
                logger.info(f"Consolidating duplicate candidate: '{threat_title}' on '{threat_asset}'")
                continue
            seen_threat_keys.add(dedup_key)

            # Retrieve threat-specific supporting evidence
            threat_queries = [threat_title, f"{threat_title} {threat_asset}", f"{threat_surface} {threat_title}"]
            specific_citations = []
            seen_chunk: set = set()
            for tq in threat_queries:
                for c in retriever.retrieve(tq, top_k=2):
                    cid = f"{c.document_name}-{c.chunk_text[:30]}"
                    if cid not in seen_chunk and getattr(c, 'relevance_score', 1.0) >= relevance_threshold:
                        c_text_lower = c.chunk_text.lower()
                        title_tokens = [tok for tok in threat_title.lower().split() if len(tok) > 2]
                        asset_tokens = [tok for tok in threat_asset.lower().split() if len(tok) > 2]

                        def token_matches(tok: str, text: str) -> bool:
                            return tok in text or any(
                                word.startswith(tok[:4]) for word in text.split() if len(tok) >= 4
                            )

                        if any(token_matches(tok, c_text_lower) for tok in title_tokens + asset_tokens):
                            seen_chunk.add(cid)
                            specific_citations.append(c)

            if specific_citations:
                evidence = specific_citations[:3]
                confidence = "Medium"
                desc = base_desc
            else:
                evidence = []
                confidence = "Low (Hypothesis)"
                missing_note = (
                    f"[Hypothesis - Unverified Scenario: Insufficient supporting evidence in knowledge base. "
                    f"Missing evidence: Threat library reference or architecture documentation confirming "
                    f"exploitation pathway for '{threat_title}' targeting '{threat_asset}' "
                    f"via '{threat_surface or 'unspecified interface'}']"
                )
                desc = f"{base_desc} {missing_note}".strip()

            valid_counter += 1
            candidate.threat_id = f"THREAT-{valid_counter:03d}"
            candidate.threat_description = desc
            candidate.evidence = evidence
            candidate.confidence = confidence
            candidate.completeness_notes()  # trigger note generation (logged, not stored)

            valid_threats.append(candidate)

        t_ground_dur = time.time() - t_ground_start
        t_total_dur = time.time() - t_start
        logger.info(
            f"[ThreatAnalysis] Completed in {t_total_dur:.2f}s "
            f"(Retr: {t_retr_dur:.2f}s, LLM: {t_llm_dur:.2f}s, Grounding: {t_ground_dur:.2f}s). "
            f"Valid candidates: {len(valid_threats)}, Rejected: {len(rejected_threats)}"
        )

    except Exception as e:
        logger.error(f"Error in generate_threats_with_rejects: {e}")

    return valid_threats, rejected_threats


def generate_threats(retriever, llm_client, assets, attack_surfaces, max_candidates: int = 5) -> list[ThreatItem]:
    """Backward-compatible wrapper — returns only valid threats."""
    valid, _rejected = generate_threats_with_rejects(
        retriever, llm_client, assets, attack_surfaces, max_candidates=max_candidates
    )
    return valid
