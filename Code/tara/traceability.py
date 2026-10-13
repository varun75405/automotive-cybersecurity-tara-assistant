class TraceabilityMatrix:
    def __init__(self):
        self.assets = []
        self.threats = []
        self.mitigations = []
        self.requirements = []
        self.risks = []
        self._asset_to_threat = {}
        self._threat_to_mitigation = {}
        self._threat_to_req = {}
        self._threat_to_risk = {}
        
    def build(self, assets, threats, mitigations, requirements, risks=None) -> dict:
        self.assets = assets or []
        # Filter invalid candidates
        self.threats = [t for t in (threats or []) if not (hasattr(t, "is_valid") and not t.is_valid())]
        self.mitigations = [m for m in (mitigations or []) if not (hasattr(m, "is_valid") and not m.is_valid())]
        self.requirements = requirements or []
        self.risks = risks or []
        
        self._asset_to_threat = {a.name: [] for a in self.assets}
        for t in self.threats:
            if t.asset in self._asset_to_threat:
                self._asset_to_threat[t.asset].append(t)
            else:
                self._asset_to_threat[t.asset] = [t]
                
        self._threat_to_mitigation = {t.threat_id: [] for t in self.threats}
        for m in self.mitigations:
            if m.threat_id in self._threat_to_mitigation:
                self._threat_to_mitigation[m.threat_id].append(m)
                
        self._threat_to_req = {t.threat_id: [] for t in self.threats}
        for r in self.requirements:
            if r.threat_id in self._threat_to_req:
                self._threat_to_req[r.threat_id].append(r)

        self._threat_to_risk = {r.threat_id: r for r in self.risks}
                
        return {
            "assets": len(self.assets),
            "threats": len(self.threats),
            "mitigations": len(self.mitigations),
            "requirements": len(self.requirements),
            "risks": len(self.risks)
        }
        
    def get_trace_for_asset(self, asset_name) -> dict:
        related_threats = self._asset_to_threat.get(asset_name, [])
        threat_ids = [t.threat_id for t in related_threats]
        
        related_mits = [m for m in self.mitigations if m.threat_id in threat_ids]
        related_reqs = [r for r in self.requirements if r.threat_id in threat_ids]
        related_risks = [r for r in self.risks if r.threat_id in threat_ids]
        
        return {
            "asset_name": asset_name,
            "threats": related_threats,
            "risks": related_risks,
            "mitigations": related_mits,
            "requirements": related_reqs
        }
        
    def get_trace_for_threat(self, threat_id) -> dict:
        related_mits = [m for m in self.mitigations if m.threat_id == threat_id]
        related_reqs = [r for r in self.requirements if r.threat_id == threat_id]
        related_risk = self._threat_to_risk.get(threat_id)
        
        return {
            "threat_id": threat_id,
            "risk": related_risk,
            "mitigations": related_mits,
            "requirements": related_reqs
        }
        
    def to_table(self) -> list[dict]:
        table = []
        for a in self.assets:
            threats = self._asset_to_threat.get(a.name, [])
            if not threats:
                table.append({
                    "Asset": a.name,
                    "Attack Surface": "N/A",
                    "Threat": None,
                    "Impact": "N/A",
                    "Feasibility": "N/A",
                    "Risk Score": "N/A",
                    "Supporting Evidence": "N/A",
                    "Mitigation": None,
                    "Requirement": None,
                    "Review Status": a.review_status
                })
                continue  # skip threat loop — no threats for this asset
            for t in threats:
                mits = self._threat_to_mitigation.get(t.threat_id, [])
                reqs = self._threat_to_req.get(t.threat_id, [])
                risk = self._threat_to_risk.get(t.threat_id)

                impact_str = f"Score {risk.impact_score}" if risk else "N/A"
                feas_str = f"{risk.attack_feasibility}" if risk else "N/A"
                risk_str = f"{risk.risk_score} ({risk.risk_level})" if risk else "N/A"

                if t.evidence:
                    doc_names = sorted(list(set(c.document_name for c in t.evidence)))
                    ev_str = ", ".join(doc_names)
                else:
                    ev_str = "None (Hypothesis)"

                if not mits and not reqs:
                    table.append({
                        "Asset": a.name,
                        "Attack Surface": t.attack_surface,
                        "Threat": t.threat_id,
                        "Threat Name": t.threat,
                        "Impact": impact_str,
                        "Feasibility": feas_str,
                        "Risk Score": risk_str,
                        "Supporting Evidence": ev_str,
                        "Mitigation": None,
                        "Requirement": None,
                        "Review Status": t.review_status
                    })
                
                for m in mits:
                    r_texts = [r.requirement_id for r in reqs]
                    table.append({
                        "Asset": a.name,
                        "Attack Surface": t.attack_surface,
                        "Threat": t.threat_id,
                        "Threat Name": t.threat,
                        "Impact": impact_str,
                        "Feasibility": feas_str,
                        "Risk Score": risk_str,
                        "Supporting Evidence": ev_str,
                        "Mitigation": m.mitigation_id,
                        "Mitigation Control": m.recommended_control,
                        "Requirement": ", ".join(r_texts) if r_texts else None,
                        "Review Status": t.review_status
                    })
        return table

    def to_full_traceability_table(self) -> list[dict]:
        """Return comprehensive traceability rows linking all required lifecycle dimensions."""
        rows = []
        for t in self.threats:
            risk = self._threat_to_risk.get(t.threat_id)
            mits = self._threat_to_mitigation.get(t.threat_id, [])
            reqs = self._threat_to_req.get(t.threat_id, [])

            impact_str = (
                f"S:{risk.impact.safety} F:{risk.impact.financial} "
                f"P:{risk.impact.privacy} A:{risk.impact.availability} (Max: {risk.impact_score})"
            ) if risk else "Unassessed"
            feas_str = f"{risk.attack_feasibility} (Score: {risk.feasibility_score})" if risk else "Unassessed"
            risk_str = f"{risk.risk_score} ({risk.risk_level})" if risk else "Unassessed"

            if t.evidence:
                doc_names = sorted(list(set(c.document_name for c in t.evidence)))
                ev_str = f"{len(t.evidence)} citation(s) from {', '.join(doc_names)}"
            else:
                ev_str = "Hypothesis (No knowledge-base citations)"

            mit_str = "; ".join([f"{m.mitigation_id}: {m.recommended_control}" for m in mits]) if mits else "None recommended"
            req_str = "; ".join([r.requirement_id for r in reqs]) if reqs else "None generated"

            rows.append({
                "Asset": t.asset,
                "Attack Surface": t.attack_surface,
                "Threat": f"{t.threat_id}: {t.threat}",
                "Impact": impact_str,
                "Feasibility": feas_str,
                "Risk Score": risk_str,
                "Supporting Evidence": ev_str,
                "Mitigation": mit_str,
                "Requirement": req_str,
                "Review Status": t.review_status
            })
        return rows
        
    def get_coverage_stats(self) -> dict:
        assets_with_threats = sum(1 for a in self.assets if len(self._asset_to_threat.get(a.name, [])) > 0)
        threats_with_mits = sum(1 for t in self.threats if len(self._threat_to_mitigation.get(t.threat_id, [])) > 0)
        threats_with_risks = sum(1 for t in self.threats if t.threat_id in self._threat_to_risk)
        
        return {
            "assets_covered": assets_with_threats,
            "total_assets": len(self.assets),
            "threats_mitigated": threats_with_mits,
            "threats_assessed": threats_with_risks,
            "total_threats": len(self.threats)
        }
