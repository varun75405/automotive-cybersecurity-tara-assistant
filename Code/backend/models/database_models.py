"""SQLAlchemy ORM models for the TARA application."""
import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.database.connection import Base


class Project(Base):
    """Project metadata."""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, default="Default Project")
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    findings = relationship("TARAFinding", back_populates="project", cascade="all, delete-orphan")


class Document(Base):
    """Uploaded document record."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    document_name = Column(String(500), nullable=False)
    document_type = Column(String(50), nullable=False)  # pdf, txt, md
    source_type = Column(String(100), default="user_upload")  # user_upload, sample_data
    file_path = Column(Text, default="")
    file_size = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    is_indexed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="documents")


class AuditLog(Base):
    """Audit log for user actions, queries, and AI responses."""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String(100), nullable=False)  # upload, query, tara_analysis, review, export
    user = Column(String(100), default="default_user")
    document_name = Column(String(500), default="")
    query = Column(Text, default="")
    retrieved_sources = Column(Text, default="")  # JSON list of source citations
    ai_response = Column(Text, default="")
    review_decision = Column(String(50), default="")  # accept, edit, reject, needs_review
    details = Column(Text, default="")  # Additional details as JSON
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class TARAFinding(Base):
    """TARA finding — assets, threats, risks, mitigations, requirements."""
    __tablename__ = "tara_findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    finding_type = Column(String(50), nullable=False)  # asset, trust_boundary, attack_surface, threat, risk, mitigation, requirement
    finding_id = Column(String(100), default="")  # e.g., ASSET-001, THREAT-001
    title = Column(String(500), default="")
    description = Column(Text, default="")
    details = Column(Text, default="")  # JSON with type-specific details
    evidence = Column(Text, default="")  # JSON list of evidence citations
    confidence = Column(String(20), default="Medium")  # High, Medium, Low
    risk_score = Column(Float, default=0.0)
    review_status = Column(String(50), default="needs_review")  # needs_review, accepted, edited, rejected
    review_comment = Column(Text, default="")
    related_finding_ids = Column(Text, default="")  # JSON list of related finding IDs for traceability
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="findings")


class ReviewDecision(Base):
    """Individual review decisions on findings."""
    __tablename__ = "review_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    finding_id = Column(Integer, ForeignKey("tara_findings.id"), nullable=False)
    decision = Column(String(50), nullable=False)  # accept, edit, reject, needs_review
    comment = Column(Text, default="")
    reviewer = Column(String(100), default="default_user")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
