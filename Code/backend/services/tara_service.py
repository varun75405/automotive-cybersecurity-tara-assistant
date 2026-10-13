from sqlalchemy.orm import Session
from backend.models.database_models import TARAFinding, AuditLog, ReviewDecision

class TARAService:
    @staticmethod
    def run_full_analysis(db: Session, project_id: int):
        from rag.retriever import Retriever
        from rag.llm_client import LLMClient
        from rag.vector_store import VectorStore
        from rag.embeddings import EmbeddingModel
        from tara import asset_analysis, threat_analysis, risk_engine
        
        embed_model = EmbeddingModel()
        vector_store = VectorStore(embed_model)
        retriever = Retriever(vector_store)
        llm = LLMClient()
        
        # 1. Assets
        assets = asset_analysis.analyze_assets(retriever, llm)
        
        # Save assets
        for a in assets:
            finding = TARAFinding(
                project_id=project_id,
                finding_type="asset",
                title=a.name,
                description=a.description,
                data=a.dict()
            )
            db.add(finding)
            
        db.commit()
        
        log = AuditLog(project_id=project_id, action="tara_analysis", details="Completed full analysis")
        db.add(log)
        db.commit()
        
        return {"status": "success", "assets_found": len(assets)}
        
    @staticmethod
    def update_finding_review(db: Session, finding_id: int, status: str, comments: str):
        decision = ReviewDecision(
            finding_id=finding_id,
            reviewer_id=1,
            status=status,
            comments=comments
        )
        db.add(decision)
        
        finding = db.query(TARAFinding).filter(TARAFinding.id == finding_id).first()
        if finding:
            log = AuditLog(
                project_id=finding.project_id, 
                action="review_update", 
                details=f"Finding {finding_id} status updated to {status}"
            )
            db.add(log)
            
        db.commit()
