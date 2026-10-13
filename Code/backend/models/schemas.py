"""Pydantic schemas for API request/response validation and data transfer."""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ── Citation / Evidence ──────────────────────────────────────────

class Citation(BaseModel):
    """A single evidence citation from a retrieved document."""
    document_name: str = ""
    page_number: Optional[int] = None
    section: str = ""
    chunk_text: str = ""
    relevance_score: float = 0.0

    def display_string(self) -> str:
        parts = [self.document_name]
        if self.page_number:
            parts.append(f"Page {self.page_number}")
        if self.section:
            parts.append(f"Section: {self.section}")
        return " — ".join(parts)


# ── Asset ────────────────────────────────────────────────────────

class AssetItem(BaseModel):
    asset_id: str = ""
    name: str = ""
    asset_type: str = ""  # ECU, Interface, Sensor, Actuator, Data, Software
    description: str = ""
    related_ecu: str = ""
    related_interface: str = ""
    security_properties: list[str] = Field(default_factory=list)  # C, I, A, Authenticity
    evidence: list[Citation] = Field(default_factory=list)
    confidence: str = "Medium"
    review_status: str = "needs_review"


# ── Trust Boundary ───────────────────────────────────────────────

class TrustBoundaryItem(BaseModel):
    boundary_id: str = ""
    name: str = ""
    connected_components: list[str] = Field(default_factory=list)
    rationale: str = ""
    evidence: list[Citation] = Field(default_factory=list)
    confidence: str = "Medium"
    review_status: str = "needs_review"


# ── Attack Surface ──────────────────────────────────────────────

class AttackSurfaceItem(BaseModel):
    surface_id: str = ""
    interface: str = ""
    connected_component: str = ""
    exposure: str = ""  # External, Internal, Physical
    security_concern: str = ""
    evidence: list[Citation] = Field(default_factory=list)
    confidence: str = "Medium"
    review_status: str = "needs_review"


# ── Threat ───────────────────────────────────────────────────────

class ThreatItem(BaseModel):
    threat_id: str = ""
    asset: str = ""
    attack_surface: str = ""
    threat: str = ""
    threat_description: str = ""
    potential_impact: str = ""
    preconditions: str = ""
    evidence: list[Citation] = Field(default_factory=list)
    confidence: str = "Medium"
    review_status: str = "needs_review"
    rejection_reason: str = ""  # populated when a candidate is rejected/excluded

    # ── Completeness thresholds ──────────────────────────────────
    _SENTINEL_VALUES: set = {"none", "null", "unknown", "n/a", "undefined", "unspecified", "tbd"}

    def _is_empty_or_sentinel(self, value: str) -> bool:
        return not value or value.strip().lower() in self._SENTINEL_VALUES

    def is_valid(self) -> bool:
        """Return True only when all core threat fields are meaningful.

        Rejects:
        - Empty or sentinel threat names (None, null, unknown, n/a, etc.)
        - Empty or sentinel target assets
        - Explicitly invalid attack surface markers (None, null, undefined)
        - Missing technical description (empty or sentinel)
        - Missing potential impact (empty or sentinel)
        The preconditions field may be omitted at threat-generation time without
        invalidating the record; callers must document uncertainty explicitly.
        """
        if self._is_empty_or_sentinel(self.threat):
            return False
        if self._is_empty_or_sentinel(self.asset):
            return False
        if self.attack_surface and self.attack_surface.strip().lower() in {"none", "null", "undefined"}:
            return False
        if self._is_empty_or_sentinel(self.threat_description):
            return False
        if self._is_empty_or_sentinel(self.potential_impact):
            return False
        return True

    def completeness_notes(self) -> list[str]:
        """Return a list of data-quality warnings for incomplete but not invalid records."""
        notes = []
        if not self.attack_surface:
            notes.append("attack_surface not specified — enter the exposed interface or bus")
        if not self.preconditions:
            notes.append("preconditions not documented — attacker capability or access requirements are missing")
        if not self.evidence:
            notes.append("no knowledge-base citations — treat as unverified hypothesis")
        return notes

    def validation_error(self) -> str:
        """Return a human-readable explanation of why this record is invalid, or 'Valid'."""
        errors = []
        if self._is_empty_or_sentinel(self.threat):
            errors.append(f"invalid threat name: '{self.threat}'")
        if self._is_empty_or_sentinel(self.asset):
            errors.append(f"invalid target asset: '{self.asset}'")
        if self.attack_surface and self.attack_surface.strip().lower() in {"none", "null", "undefined"}:
            errors.append(f"invalid attack_surface sentinel: '{self.attack_surface}'")
        if self._is_empty_or_sentinel(self.threat_description):
            errors.append("missing technical description")
        if self._is_empty_or_sentinel(self.potential_impact):
            errors.append("missing potential impact statement")
        return "; ".join(errors) if errors else "Valid"


# ── Impact Assessment ───────────────────────────────────────────

class ImpactAssessment(BaseModel):
    safety: int = 1        # 1-4
    financial: int = 1     # 1-4
    privacy: int = 1       # 1-4
    availability: int = 1  # 1-4
    rationale: str = ""


# ── Risk ─────────────────────────────────────────────────────────

class RiskItem(BaseModel):
    risk_id: str = ""
    threat_id: str = ""
    asset: str = ""
    threat: str = ""
    impact: ImpactAssessment = Field(default_factory=ImpactAssessment)
    attack_feasibility: str = "Medium"  # Low, Medium, High
    feasibility_score: int = 2  # 1, 2, 3
    impact_score: int = 1  # max of impact dimensions
    risk_score: float = 0.0  # impact_score * feasibility_score
    risk_level: str = "Medium"  # Critical, High, Medium, Low
    scoring_rationale: str = ""
    evidence: list[Citation] = Field(default_factory=list)
    review_status: str = "needs_review"


# ── Mitigation ──────────────────────────────────────────────────

class MitigationItem(BaseModel):
    mitigation_id: str = ""
    threat_id: str = ""
    asset: str = ""
    threat: str = ""
    recommended_control: str = ""
    control_category: str = ""  # access_control, authentication, integrity, etc.
    description: str = ""
    evidence: list[Citation] = Field(default_factory=list)
    confidence: str = "Medium"
    review_status: str = "needs_review"

    def is_valid(self) -> bool:
        """Return False only for structurally empty mitigations (no control or threat linkage)."""
        return bool(self.recommended_control and self.threat_id)


# ── Cybersecurity Requirement ───────────────────────────────────

class RequirementItem(BaseModel):
    requirement_id: str = ""
    asset: str = ""
    threat_id: str = ""
    threat: str = ""
    recommended_control: str = ""
    rationale: str = ""
    evidence: list[Citation] = Field(default_factory=list)
    review_status: str = "needs_review"
    ai_generated_note: str = "AI-generated candidate requirement — requires cybersecurity engineer approval."


# ── TARA Analysis Result ────────────────────────────────────────

class TARAResult(BaseModel):
    """Complete TARA analysis result."""
    project_name: str = ""
    analysis_timestamp: str = ""
    llm_mode: str = ""  # "REAL LLM" or "DEMO FALLBACK"
    assets: list[AssetItem] = Field(default_factory=list)
    trust_boundaries: list[TrustBoundaryItem] = Field(default_factory=list)
    attack_surfaces: list[AttackSurfaceItem] = Field(default_factory=list)
    threats: list[ThreatItem] = Field(default_factory=list)
    risks: list[RiskItem] = Field(default_factory=list)
    mitigations: list[MitigationItem] = Field(default_factory=list)
    requirements: list[RequirementItem] = Field(default_factory=list)
    disclaimer: str = "AI-generated analysis is advisory and requires qualified cybersecurity engineer review."


# ── Chat ─────────────────────────────────────────────────────────

class ChatQuery(BaseModel):
    query: str
    project_id: int = 1


class ChatResponse(BaseModel):
    answer: str = ""
    citations: list[Citation] = Field(default_factory=list)
    confidence: str = "Medium"
    llm_mode: str = ""
    disclaimer: str = "AI-generated response requires human review. Confidence is an application-level indicator, not a guaranteed probability."


# ── Document Upload ──────────────────────────────────────────────

class DocumentInfo(BaseModel):
    id: int = 0
    document_name: str = ""
    document_type: str = ""
    source_type: str = ""
    chunk_count: int = 0
    is_indexed: bool = False
    created_at: Optional[datetime] = None


# ── Evaluation ──────────────────────────────────────────────────

class EvalQuestion(BaseModel):
    id: int = 0
    question: str = ""
    expected_elements: list[str] = Field(default_factory=list)
    category: str = ""


class EvalResult(BaseModel):
    question_id: int = 0
    question: str = ""
    answer: str = ""
    citations: list[Citation] = Field(default_factory=list)
    expected_elements: list[str] = Field(default_factory=list)
    found_elements: list[str] = Field(default_factory=list)
    retrieval_relevance: float = 0.0
    groundedness: float = 0.0
    element_coverage: float = 0.0
    has_citations: bool = False
    llm_mode: str = ""
