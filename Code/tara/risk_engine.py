import sys
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.models.schemas import RiskItem, ImpactAssessment, ThreatItem

logger = logging.getLogger(__name__)

def _extract_json_string(text: str) -> str:
    """Helper to extract clean JSON from markdown fences or prefixed responses."""
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
            return text[start_obj:end_obj+1]
    return text

# ── Project-defined risk thresholds (not official ISO/SAE 21434 classifications) ──
# Score = max(Safety, Financial, Privacy, Availability) × Feasibility
# Impact dimensions: integers 1–4
#   1 = Negligible, 2 = Moderate, 3 = Major, 4 = Severe
# Feasibility: Low=1, Medium=2, High=3
# Thresholds: Score ≥9 → Critical | ≥6 → High | ≥3 → Medium | <3 → Low
# Maximum possible score: 4 × 3 = 12 (Critical)
# These thresholds are defined for this project demonstration only.
# A certified cybersecurity engineer must validate classifications before use in production.
_FEASIBILITY_MAP = {'Low': 1, 'Medium': 2, 'High': 3}
_RISK_THRESHOLD_CRITICAL = 9
_RISK_THRESHOLD_HIGH = 6
_RISK_THRESHOLD_MEDIUM = 3

def calculate_risk_score(impact: ImpactAssessment, feasibility: str) -> tuple[float, str, str]:
    feasibility_map = {'Low': 1, 'Medium': 2, 'High': 3}
    
    if feasibility not in feasibility_map:
        return 0.0, "Unresolved (Input Validation Failed)", f"Feasibility '{feasibility}' is unassessed or invalid. Risk score cannot be calculated."
    
    # Strictly validate impact dimensions: must be genuine int in 1-4, not boolean, not float
    dim_errors = []
    for dim_name in ["safety", "financial", "privacy", "availability"]:
        val = getattr(impact, dim_name, None)
        if isinstance(val, bool) or not isinstance(val, int) or isinstance(val, float):
            dim_errors.append(f"{dim_name}={val!r} is not an integer")
        elif not (1 <= val <= 4):
            dim_errors.append(f"{dim_name}={val} is outside supported range 1-4")
            
    if dim_errors:
        return 0.0, "Unresolved (Input Validation Failed)", f"Impact validation failed: {'; '.join(dim_errors)}. Risk score cannot be calculated."
        
    feasibility_score = feasibility_map[feasibility]
    impact_score = max(impact.safety, impact.financial, impact.privacy, impact.availability)
    
    risk_score = impact_score * feasibility_score
    
    if risk_score >= 9:
        risk_level = 'Critical'
    elif risk_score >= 6:
        risk_level = 'High'
    elif risk_score >= 3:
        risk_level = 'Medium'
    else:
        risk_level = 'Low'
        
    rationale = (
        f"Impact score is max(S:{impact.safety}, F:{impact.financial}, P:{impact.privacy}, A:{impact.availability}) = {impact_score}. "
        f"Feasibility '{feasibility}' maps to {feasibility_score}. Risk Score = {impact_score} * {feasibility_score} = {risk_score} ({risk_level})."
    )
    
    return float(risk_score), risk_level, rationale

def assess_risks(threats: list[ThreatItem], retriever, llm_client) -> list[RiskItem]:
    risks = []
    try:
        for threat in threats:
            # Strictly validate threat candidate: reject incomplete or invalid candidates
            if not getattr(threat, "is_valid", lambda: True)():
                logger.warning(f"Skipping risk assessment for invalid/incomplete threat candidate: {threat.threat_id}")
                continue

            prompt = f"""
Provide a QUALITATIVE assessment for the following threat:
Threat: {threat.threat}
Target Asset: {threat.asset}
Attack Surface: {threat.attack_surface}
Description: {threat.threat_description}

Provide JSON with:
- safety (integer 1-4: 1=negligible, 2=minor, 3=moderate/severe injury, 4=fatal/life-threatening)
- financial (integer 1-4)
- privacy (integer 1-4)
- availability (integer 1-4)
- rationale (string explaining why these dimensions were chosen)
- feasibility ('Low', 'Medium', or 'High')
"""
            response = llm_client.generate(prompt=prompt, system_prompt="You are an expert automotive cybersecurity risk assessor. Output strictly valid JSON.")
            
            parsing_failed = False
            try:
                json_str = _extract_json_string(response)
                parsed = json.loads(json_str)
                if not isinstance(parsed, dict):
                    parsing_failed = True
                    parsed = {}
            except Exception as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                parsing_failed = True
                parsed = {}

            if parsing_failed:
                # Do NOT silently produce a misleading Low (1.0) risk score
                impact = ImpactAssessment(
                    safety=0,
                    financial=0,
                    privacy=0,
                    availability=0,
                    rationale="[ERROR: AI qualitative assessment parsing failed. Requires manual assessment.]"
                )
                feasibility = "Unknown"
                risk_score = 0.0
                risk_level = "Unresolved (Parsing Error)"
                scoring_rationale = (
                    f"Qualitative impact and feasibility could not be determined because LLM response parsing failed. "
                    f"Risk score was not computed to avoid misleading low scores. Manual engineer assessment is required."
                )
                review_status = "needs_review (parsing_error)"
                feasibility_score = 0
                impact_score = 0
            else:
                # Validate each dimension strictly — no silent replacement with default 1
                dim_errors = []
                raw_dims = {}
                for dim in ["safety", "financial", "privacy", "availability"]:
                    raw = parsed.get(dim)
                    if raw is None:
                        dim_errors.append(f"{dim} is missing")
                    elif isinstance(raw, bool):
                        dim_errors.append(f"{dim}={raw!r} is a boolean, not an integer")
                    elif isinstance(raw, float):
                        dim_errors.append(f"{dim}={raw!r} is a float/fractional value, not an integer")
                    elif isinstance(raw, int):
                        if not (1 <= raw <= 4):
                            dim_errors.append(f"{dim}={raw} is outside supported range 1-4")
                        else:
                            raw_dims[dim] = raw
                    elif isinstance(raw, str):
                        raw_str = raw.strip()
                        # Strict integer string check (no decimals, no scientific notation)
                        if raw_str.isdigit():
                            v = int(raw_str)
                            if not (1 <= v <= 4):
                                dim_errors.append(f"{dim}={v} is outside supported range 1-4")
                            else:
                                raw_dims[dim] = v
                        else:
                            dim_errors.append(f"{dim}={raw!r} is not an integer")
                    else:
                        dim_errors.append(f"{dim}={raw!r} is not an integer")

                raw_feas = str(parsed.get("feasibility", "")).strip()
                if raw_feas not in ('Low', 'Medium', 'High'):
                    dim_errors.append(f"feasibility='{raw_feas}' is not one of Low/Medium/High")

                if dim_errors:
                    # Missing or out-of-range inputs → unresolved, no numeric score
                    impact = ImpactAssessment(
                        safety=0, financial=0, privacy=0, availability=0,
                        rationale=f"[UNRESOLVED: input validation failed — {'; '.join(dim_errors)}]"
                    )
                    feasibility = "Unknown"
                    risk_score = 0.0
                    risk_level = "Unresolved (Input Validation Failed)"
                    scoring_rationale = (
                        f"Risk score cannot be calculated: {'; '.join(dim_errors)}. "
                        "Manual cybersecurity engineer assessment is required."
                    )
                    review_status = "needs_review (input_validation_failed)"
                    feasibility_score = 0
                    impact_score = 0
                else:
                    s_val = raw_dims["safety"]
                    f_val = raw_dims["financial"]
                    p_val = raw_dims["privacy"]
                    a_val = raw_dims["availability"]

                    impact = ImpactAssessment(
                        safety=s_val, financial=f_val, privacy=p_val, availability=a_val,
                        rationale=str(parsed.get("rationale", "")).strip()
                    )
                    feasibility = raw_feas
                    risk_score, risk_level, scoring_rationale = calculate_risk_score(impact, feasibility)
                    feasibility_map = {'Low': 1, 'Medium': 2, 'High': 3}
                    feasibility_score = feasibility_map[feasibility]
                    impact_score = max(s_val, f_val, p_val, a_val)
                    review_status = "needs_review"
            
            risks.append(RiskItem(
                risk_id=f"RISK-{threat.threat_id.split('-')[-1]}",
                threat_id=threat.threat_id,
                asset=threat.asset,
                threat=threat.threat,
                impact=impact,
                attack_feasibility=feasibility,
                feasibility_score=feasibility_score,
                impact_score=impact_score,
                risk_score=risk_score,
                risk_level=risk_level,
                scoring_rationale=scoring_rationale,
                evidence=threat.evidence,
                review_status=review_status
            ))
    except Exception as e:
        logger.error(f"Error in assess_risks: {e}")

    return risks
