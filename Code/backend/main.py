import sys
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database.connection import init_db
from backend.api import documents, tara, chat, reports

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize db
    init_db()
    yield
    # Shutdown

app = FastAPI(title="TARA API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(tara.router, prefix="/api/tara", tags=["tara"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])

@app.get("/")
def root():
    return {"message": "TARA API is running"}
