from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import os
import shutil
from pathlib import Path
from backend.database.connection import get_db
from backend.models.database_models import Document, AuditLog
from backend.services.document_service import DocumentService

router = APIRouter()

@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    project_id: int = 1,
    source_type: str = "specification",
    db: Session = Depends(get_db)
):
    valid_extensions = {".pdf", ".txt", ".md"}
    ext = Path(file.filename).suffix.lower()
    if ext not in valid_extensions:
        raise HTTPException(status_code=400, detail="Invalid file type. Only pdf, txt, md allowed.")
    
    # Save file
    upload_dir = Path("c:/TARA/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    file_size = os.path.getsize(file_path)
    if file_size > 50 * 1024 * 1024:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit.")

    try:
        doc = DocumentService.process_document(
            db=db, 
            file_path=str(file_path), 
            filename=file.filename, 
            project_id=project_id, 
            source_type=source_type
        )
        return {"message": "Document uploaded and processed", "doc_id": doc.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index-samples")
def index_samples(project_id: int = 1, db: Session = Depends(get_db)):
    try:
        DocumentService.index_sample_data(db, project_id)
        return {"message": "Sample data indexed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).all()
    return docs

@router.get("/{doc_id}")
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.delete("/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    try:
        DocumentService.delete_document(db, doc_id)
        return {"message": "Document deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
