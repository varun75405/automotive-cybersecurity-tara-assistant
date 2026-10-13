from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.services.tara_service import TARAService
from backend.models.database_models import TARAFinding

router = APIRouter()

@router.post("/analyze")
def run_analysis(project_id: int = 1, db: Session = Depends(get_db)):
    try:
        result = TARAService.run_full_analysis(db, project_id)
        return {"message": "Analysis completed", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/assets")
def get_assets(project_id: int = 1, db: Session = Depends(get_db)):
    findings = db.query(TARAFinding).filter_by(project_id=project_id, finding_type="asset").all()
    return findings

@router.get("/threats")
def get_threats(project_id: int = 1, db: Session = Depends(get_db)):
    findings = db.query(TARAFinding).filter_by(project_id=project_id, finding_type="threat").all()
    return findings

@router.get("/risks")
def get_risks(project_id: int = 1, db: Session = Depends(get_db)):
    findings = db.query(TARAFinding).filter_by(project_id=project_id, finding_type="risk").all()
    return findings

@router.put("/review/{finding_id}")
def update_review(finding_id: int, status: str, comments: str = "", db: Session = Depends(get_db)):
    try:
        TARAService.update_finding_review(db, finding_id, status, comments)
        return {"message": "Review updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
