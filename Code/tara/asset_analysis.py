import sys
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.models.schemas import AssetItem

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
        elif isinstance(parsed, dict) and "assets" in parsed and isinstance(parsed["assets"], list):
            return parsed["assets"]
    except Exception:
        pass
    return []

# Allowed asset_type values that the pipeline supports
_ALLOWED_ASSET_TYPES = {
    "ECU", "Hardware Security Component", "Interface / Bus",
    "Network", "Antenna", "Sensor", "Actuator"
}

# Map known hardware security component name fragments to the correct type
_HSM_NAME_FRAGMENTS = {"hardware security module", "hsm", "secure element", "security controller", "shse", "she "}


def _sanitize_asset_type(name: str, proposed_type: str) -> str:
    """Return the corrected asset_type for a given asset name and proposed type.

    Rules (applied in priority order):
    1. If the name identifies a hardware security component (HSM, Secure Element),
       classify it as 'Hardware Security Component' regardless of proposed_type.
    2. Reject 'Mitigation' as an asset_type — it is a control category, not a component.
       An item whose LLM-returned type is 'Mitigation' is flagged as requiring review;
       we do NOT blindly reclassify unrelated assets as hardware security components.
    3. Apply name-pattern heuristics for well-known automotive component families.
    4. If the proposed_type is already in _ALLOWED_ASSET_TYPES, accept it.
    5. Otherwise flag as 'Unknown (Requires Classification)' for engineering review.
    """
    norm = name.lower()
    # Rule 1: HSM / Secure Element — identity-based, highest priority
    if any(frag in norm for frag in _HSM_NAME_FRAGMENTS):
        return "Hardware Security Component"

    # Rule 2: 'Mitigation' is not an asset classification
    if proposed_type.strip().lower() == "mitigation":
        # Flag for review — do not assume it's a hardware security component
        return "Unknown (Requires Classification)"

    # Rule 3: name-pattern heuristics
    if "antenna" in norm:
        return "Antenna"
    if "ethernet" in norm or ("network" in norm and "security" not in norm):
        return "Network"
    if "can bus" in norm or "can-fd" in norm or "lin bus" in norm or norm.endswith(" bus"):
        return "Interface / Bus"

    # Rule 4: pass-through for recognised types
    if proposed_type.strip() in _ALLOWED_ASSET_TYPES:
        return proposed_type.strip()

    # Rule 5: unknown — flag for review
    return f"Unknown (Requires Classification — was: '{proposed_type}')"


def _sanitize_asset_item(item: AssetItem) -> AssetItem:
    """Return a corrected copy of item with a validated asset_type."""
    corrected_type = _sanitize_asset_type(item.name, item.asset_type)
    return item.model_copy(update={"asset_type": corrected_type})

def analyze_assets(retriever, llm_client) -> list[AssetItem]:
    """Identify automotive assets and CIA/A security properties from the knowledge base.

    Returns a list of AssetItem objects. Raises RuntimeError with a descriptive
    message on hard failures (empty knowledge base, LLM error) so callers can
    surface the error in the UI rather than silently returning [].
    """
    import time
    t_start = time.time()
    assets = []

    queries = ['ECU inventory', 'vehicle components', 'electronic control units']
    t_retr_start = time.time()
    all_citations = []
    for q in queries:
        all_citations.extend(retriever.retrieve(q, top_k=5, filter_metadata={}))

    seen = set()
    unique_citations = []
    for c in all_citations:
        cid = f"{c.document_name}-{c.chunk_text[:20]}"
        if cid not in seen:
            seen.add(cid)
            unique_citations.append(c)

    t_retr_dur = time.time() - t_retr_start
    logger.info(f"[AssetAnalysis] Retrieval: {len(unique_citations)} unique chunks in {t_retr_dur:.2f}s")

    # Guard: empty knowledge base
    if not unique_citations:
        raise RuntimeError(
            "No documents are indexed in the knowledge base. "
            "Please upload and index your architecture documents via the "
            "Document Upload page before running Asset Analysis."
        )

    context = "\n".join([f"Doc: {c.document_name}\nText: {c.chunk_text}" for c in unique_citations])
    logger.info(f"[AssetAnalysis] Context length: {len(context)} chars")

    prompt = f"""
Identify all automotive assets (ECUs, interfaces, networks, hardware security components, sensors, actuators) from the following context.
Allowed asset_type values:
- "ECU" (Electronic Control Unit, Domain Controller)
- "Hardware Security Component" (e.g., Hardware Security Module (HSM), Secure Element - DO NOT classify hardware as "Mitigation")
- "Interface / Bus" (e.g., CAN-FD, LIN, OBD-II)
- "Network" (e.g., Automotive Ethernet)
- "Antenna" (e.g., Cellular Antenna, GPS Antenna)
- "Sensor" (e.g., Camera, Radar, LiDAR)
- "Actuator" (e.g., Steering, Braking)

Return a JSON list of objects with keys:
- asset_id
- name
- asset_type
- description
- related_ecu
- related_interface
- security_properties (list of strings: e.g. ["Confidentiality", "Integrity", "Availability", "Authenticity"])

Context:
{context}
"""
    system_prompt = "You are an automotive cybersecurity TARA asset analyzer. Output strictly a JSON array of objects."

    t_llm_start = time.time()
    response = llm_client.generate(prompt=prompt, system_prompt=system_prompt)
    t_llm_dur = time.time() - t_llm_start
    logger.info(f"[AssetAnalysis] LLM response: {len(response)} chars in {t_llm_dur:.2f}s")

    # _extract_json_array raises RuntimeError if response contains [LIVE LLM CALL FAILED: ...]
    parsed = _extract_json_array(response)
    logger.info(f"[AssetAnalysis] Parsed {len(parsed)} raw items from LLM response")

    seen_names = set()
    skipped_sentinel = 0
    skipped_duplicate = 0
    skipped_validation_error = 0

    for i, item in enumerate(parsed):
        if isinstance(item, str):
            item = {"name": item, "asset_type": "ECU"}

        raw_name = str(item.get("name", "Unknown Asset")).strip()
        normalized_name = raw_name.replace("Celullar", "Cellular").replace("celullar", "cellular")

        norm_key = normalized_name.lower()
        if norm_key in seen_names or not normalized_name or norm_key in {"none", "null", "unknown"}:
            skipped_sentinel += 1
            continue
        seen_names.add(norm_key)

        raw_type = _sanitize_asset_type(
            normalized_name, str(item.get("asset_type", "ECU")).strip()
        )

        related_ecu = item.get("related_ecu", "")
        if isinstance(related_ecu, list):
            related_ecu = ", ".join(related_ecu)

        related_iface = item.get("related_interface", "")
        if isinstance(related_iface, list):
            related_iface = ", ".join(related_iface)

        sec_props = item.get("security_properties")
        if sec_props is None:
            sec_props = ["Integrity", "Authenticity"]
        elif isinstance(sec_props, str):
            sec_props = [s.strip() for s in sec_props.split(",") if s.strip()]
        elif isinstance(sec_props, list):
            sec_props = [str(s) for s in sec_props if s]

        # Attach citations only if content matches or if grounded in retrieved text
        searchable_text = f"{normalized_name} {related_ecu} {related_iface}".lower()
        search_tokens = [
            tok.strip("(),.-/") for tok in searchable_text.split()
            if len(tok.strip("(),.-/")) > 2
        ]
        matched_citations = [
            c for c in unique_citations
            if any(tok in c.chunk_text.lower() for tok in search_tokens)
        ]
        is_demo_run = bool(getattr(llm_client, "is_demo", False) is True or getattr(llm_client, "is_fallback_active", False) is True)

        if matched_citations:
            evidence = matched_citations[:3]
            confidence = "Medium"
        elif is_demo_run:
            evidence = []
            confidence = "Low (Demo Predefined Candidate)"
        else:
            evidence = unique_citations[:2]
            confidence = "Medium"

        try:
            assets.append(AssetItem(
                asset_id=item.get("asset_id", f"A-{(len(assets)+1):02d}"),
                name=normalized_name,
                asset_type=raw_type,
                description=str(item.get("description", "")).strip(),
                related_ecu=str(related_ecu),
                related_interface=str(related_iface),
                security_properties=sec_props,
                evidence=evidence,
                confidence=confidence,
                review_status="needs_review"
            ))
        except Exception as val_err:
            logger.error(f"[AssetAnalysis] Item {i} ({normalized_name}) validation error: {val_err}")
            skipped_validation_error += 1

    t_total = time.time() - t_start
    logger.info(
        f"[AssetAnalysis] Complete in {t_total:.2f}s "
        f"(Retr: {t_retr_dur:.2f}s, LLM: {t_llm_dur:.2f}s). "
        f"Assets: {len(assets)} valid, {skipped_sentinel} sentinel/empty, "
        f"{skipped_duplicate} duplicate, {skipped_validation_error} validation-error."
    )

    return assets
