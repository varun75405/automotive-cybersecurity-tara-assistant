import sys
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.models.schemas import RequirementItem, ThreatItem, MitigationItem

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

def generate_requirements(threats: list[ThreatItem], mitigations: list[MitigationItem], retriever, llm_client) -> list[RequirementItem]:
    requirements = []
    try:
        mitigation_map = {m.threat_id: m for m in mitigations}
        
        for i, threat in enumerate(threats):
            m = mitigation_map.get(threat.threat_id)
            if not m:
                continue
                
            prompt = f"""
Generate a candidate cybersecurity requirement for this threat-mitigation pair.
Threat: {threat.threat}
Mitigation: {m.recommended_control}
Description: {m.description}

Provide JSON with:
- requirement_text (the actual requirement)
- rationale
"""
            response = llm_client.generate(prompt=prompt, system_prompt="You are a TARA requirements generator. Output strictly JSON.")
            parsed = _extract_json_object(response)
                
            req_text = parsed.get("requirement_text", f"The system shall implement {m.recommended_control} for {threat.asset}.")
            rationale_field = parsed.get("rationale", f"Mitigates {threat.threat} on {threat.attack_surface}.")
            rationale_text = f"Requirement: {req_text}\nRationale: {rationale_field}"
            
            requirements.append(RequirementItem(
                requirement_id=f"REQ-{(i+1):03d}",
                asset=threat.asset,
                threat_id=threat.threat_id,
                threat=threat.threat,
                recommended_control=m.recommended_control,
                rationale=rationale_text,
                evidence=threat.evidence,
                review_status="needs_review",
                ai_generated_note='AI-generated candidate requirement — requires cybersecurity engineer approval.'
            ))
    except Exception as e:
        logger.error(f"Error in generate_requirements: {e}")

    return requirements
