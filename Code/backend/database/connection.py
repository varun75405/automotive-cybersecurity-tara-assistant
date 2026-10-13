"""Database connection and session management for SQLite."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

_engine = None
_SessionLocal = None


class Base(DeclarativeBase):
    pass


def get_engine(db_path: str = None):
    """Get or create the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        if db_path is None:
            from config import get_settings
            db_path = get_settings().sqlite_db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        _engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,
            connect_args={"check_same_thread": False}
        )
    return _engine


def get_session_factory(db_path: str = None) -> sessionmaker:
    """Get session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine(db_path)
        _SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return _SessionLocal


def get_db() -> Session:
    """Get a database session (use as context manager or dependency)."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


def init_db(db_path: str = None):
    """Initialize database — create all tables."""
    from backend.models.database_models import (
        Base, Project, Document, AuditLog, TARAFinding, ReviewDecision
    )
    engine = get_engine(db_path)
    Base.metadata.create_all(bind=engine)


def log_audit_event(
    action: str,
    user: str = "security_engineer",
    document_name: str = "",
    query: str = "",
    retrieved_sources: str = "",
    ai_response: str = "",
    review_decision: str = "",
    details: str = ""
):
    """Log an audit event to the audit_log SQLite table."""
    try:
        from backend.models.database_models import AuditLog
        factory = get_session_factory()
        session = factory()
        log_entry = AuditLog(
            action=action,
            user=user,
            document_name=document_name,
            query=query,
            retrieved_sources=retrieved_sources,
            ai_response=ai_response,
            review_decision=review_decision,
            details=details,
        )
        session.add(log_entry)
        session.commit()
        session.close()
    except Exception as e:
        # Avoid crashing app if logging fails
        print(f"[AuditLog Error] Failed to log action {action}: {e}")

