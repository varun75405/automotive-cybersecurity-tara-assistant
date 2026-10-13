import streamlit as st
from backend.database.connection import log_audit_event

def render_review_controls(key, current_status='needs_review', item_type='finding'):
    options = ['needs_review', 'accepted', 'edited', 'rejected']
    idx = options.index(current_status) if current_status in options else 0
    new_status = st.selectbox('Review Status', options, index=idx, key=f'review_{key}')
    if new_status != current_status:
        log_audit_event(
            action="review_decision",
            user="security_engineer",
            review_decision=new_status,
            details=f"Item {key} ({item_type}) status changed from {current_status} to {new_status}"
        )
    return new_status

