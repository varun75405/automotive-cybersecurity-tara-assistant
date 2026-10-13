import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.resolve()))

import streamlit as st
import pandas as pd
from backend.database.connection import get_engine, get_session_factory, init_db
from backend.models.database_models import AuditLog
from sqlalchemy import select, desc
from frontend.init_state import ensure_session_state, render_sidebar

settings, embedding_model, vector_store, retriever, llm_client = ensure_session_state()
render_sidebar()

st.title("SQLite Audit Trail & Review Analytics")
st.markdown("Inspect persistent audit records of document uploads, user queries, TARA analysis executions, and engineer review decisions.")

try:
    init_db(settings.sqlite_db_path)
    engine = get_engine(settings.sqlite_db_path)
    SessionFactory = get_session_factory(settings.sqlite_db_path)
    
    with SessionFactory() as session:
        logs = session.execute(select(AuditLog).order_by(desc(AuditLog.timestamp))).scalars().all()
        
    data = []
    for log in logs:
        data.append({
            "ID": log.id,
            "Timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "N/A",
            "Action": log.action,
            "User": log.user,
            "Document": log.document_name or "N/A",
            "Details": log.details or "N/A"
        })
        
    if data:
        st.subheader(f"Logged Audit Records ({len(data)})")
        df_logs = pd.DataFrame(data)
        st.dataframe(df_logs, use_container_width=True)
    else:
        st.info("No audit logs recorded yet in the database. As you upload documents and run analyses, audit entries will appear here.")
        
except Exception as e:
    st.error(f"Error loading audit logs: {e}")
