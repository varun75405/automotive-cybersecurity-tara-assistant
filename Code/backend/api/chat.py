from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.models.database_models import AuditLog

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    project_id: int = 1

@router.post("/query")
def chat_query(req: ChatRequest, db: Session = Depends(get_db)):
    try:
        from rag.retriever import Retriever
        from rag.llm_client import LLMClient
        from rag.vector_store import VectorStore
        from rag.embeddings import EmbeddingModel
        
        embed_model = EmbeddingModel()
        vector_store = VectorStore(embed_model)
        retriever = Retriever(vector_store)
        llm = LLMClient()
        
        citations = retriever.retrieve(req.query, top_k=5, filter_metadata={"project_id": req.project_id})
        
        context = "\n".join([f"[{c.document_id}]: {c.content}" for c in citations])
        prompt = f"Context:\n{context}\n\nQuery: {req.query}"
        
        response = llm.generate(prompt, "You are a helpful TARA assistant.")
        
        # Log action
        log = AuditLog(project_id=req.project_id, action="chat_query", details=f"Query: {req.query}")
        db.add(log)
        db.commit()
        
        return {"response": response, "citations": [c.dict() for c in citations]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
