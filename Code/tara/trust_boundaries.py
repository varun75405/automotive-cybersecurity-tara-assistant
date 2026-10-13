import sys
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.models.schemas import TrustBoundaryItem

logger = logging.getLogger(__name__)

def _extract_json_array(text: str) -> list:
    """Helper to safely extract JSON list from LLM output."""
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
        elif isinstance(parsed, dict) and "boundaries" in parsed and isinstance(parsed["boundaries"], list):
            return parsed["boundaries"]
    except Exception:
        pass
    return []

def identify_trust_boundaries(retriever, llm_client) -> list[TrustBoundaryItem]:
    boundaries = []
    try:
        queries = ['trust boundary info', 'network zones', 'security domains']
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

        context = "\n".join([f"Doc: {c.document_name}\nText: {c.chunk_text}" for c in unique_citations])
        
        prompt = f"""
Identify all trust boundaries from the following context.
Return a JSON list of objects with keys:
- boundary_id
- name
- connected_components (list of strings)
- rationale

Context:
{context}
"""
        response = llm_client.generate(prompt=prompt, system_prompt="You are a TARA trust boundary analyzer. Output strictly JSON array of objects.")
        parsed = _extract_json_array(response)

        for item in parsed:
            if isinstance(item, str):
                item = {"name": item, "rationale": item}
                
            connected = item.get("connected_components", [])
            if isinstance(connected, str):
                connected = [connected]

            boundary_name = item.get("name", "Unknown Boundary")

            # ── Evidence grounding: filter citations by relevance to this boundary ──
            search_terms = set()
            for tok in boundary_name.lower().split():
                if len(tok) >= 3:
                    search_terms.add(tok)
            for comp in connected:
                for tok in str(comp).lower().split():
                    if len(tok) >= 3:
                        search_terms.add(tok)

            matched_citations = []
            if search_terms:
                for cit in unique_citations:
                    cit_lower = cit.chunk_text.lower()
                    if any(term in cit_lower for term in search_terms):
                        matched_citations.append(cit)

            if matched_citations:
                evidence = matched_citations[:3]
                confidence = "Medium"
            else:
                is_demo_run = getattr(llm_client, 'is_demo', False) or getattr(llm_client, 'is_fallback_active', False)
                evidence = []
                confidence = "Low (Demo Predefined Candidate)" if is_demo_run else "Low (Unverified)"

            boundaries.append(TrustBoundaryItem(
                boundary_id=item.get("boundary_id", f"TB-{(len(boundaries)+1):02d}"),
                name=boundary_name,
                connected_components=connected,
                rationale=item.get("rationale", ""),
                evidence=evidence,
                confidence=confidence,
                review_status="needs_review"
            ))
    except Exception as e:
        logger.error(f"Error in identify_trust_boundaries: {e}")

    return boundaries
