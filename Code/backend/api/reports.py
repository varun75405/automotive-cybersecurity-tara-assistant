from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.services.report_service import ReportService
import os

router = APIRouter()

@router.post("/generate")
def generate_report(project_id: int = 1, format: str = "markdown", db: Session = Depends(get_db)):
    try:
        filename = ReportService.generate_report(db, project_id, format)
        return {"message": "Report generated", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{filename}")
def download_report(filename: str):
    file_path = f"c:/TARA/reports/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(file_path, filename=filename)
