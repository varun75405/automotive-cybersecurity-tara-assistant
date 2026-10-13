import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.resolve()))

import time
import streamlit as st
import pandas as pd
from tara.attack_surface import analyze_attack_surfaces
from tara.asset_analysis import analyze_assets
from frontend.components.citations import render_citations
from frontend.components.review_controls import render_review_controls
from frontend.init_state import ensure_session_state, render_sidebar

settings, embedding_model, vector_store, retriever, llm_client = ensure_session_state()
render_sidebar()

st.title("Attack Surface Analysis")
st.caption(
    "ℹ️ **Analysis Scope:** Identifies vehicle attack surfaces across physical interfaces "
    "(OBD-II, USB), wireless connectivity (Telematics, OTA, V2X, Bluetooth), and internal "
    "buses. Results are candidate findings for qualified cybersecurity engineering review."
)

# ── Pre-flight: knowledge-base status ───────────────────────────────────────
doc_count = vector_store.get_document_count()
if doc_count == 0:
    st.warning(
        "⚠️ **Knowledge base is empty.** Attack surface analysis requires indexed "
        "architecture documents. Please upload and index documents on the "
        "**Document Upload** page first."
    )

if 'assets' not in st.session_state:
    st.info(
        "ℹ️ Asset Analysis has not been run yet. "
        "Clicking the button below will run Asset Analysis automatically first."
    )

if st.button("Run Attack Surface Analysis", type="primary", disabled=(doc_count == 0)):
    t_page_start = time.time()
    analysis_succeeded = False
    try:
        status_box = st.status("Analyzing vehicle attack surfaces...", expanded=True)
        with status_box:
            # Step 1: Assets (reuse if already cached)
            if 'assets' not in st.session_state or not st.session_state.assets:
                st.write("Step 1/2: Identifying vehicle assets...")
                st.session_state.assets = analyze_assets(retriever, llm_client)
                st.write(f"  ✓ {len(st.session_state.assets)} assets identified.")
            else:
                st.write(f"Step 1/2: Using {len(st.session_state.assets)} cached assets.")

            # Step 2: Attack surfaces
            st.write("Step 2/2: Mapping communication interface attack surfaces...")
            surfaces = analyze_attack_surfaces(
                retriever, llm_client, st.session_state.assets
            )
            st.session_state.attack_surfaces = surfaces
            analysis_succeeded = True

        t_elapsed = time.time() - t_page_start

        from backend.database.connection import log_audit_event
        log_audit_event(
            action="attack_surface_analysis",
            user="security_engineer",
            details=(
                f"Identified {len(surfaces)} attack surfaces in {t_elapsed:.1f}s. "
                f"Mode: {llm_client.mode}"
            ),
        )

        if len(surfaces) == 0:
            # Succeeded but genuinely found nothing — distinguish from a failure
            status_box.update(
                label="Attack surface analysis complete — 0 surfaces found.",
                state="complete",
                expanded=True,
            )
            st.warning(
                f"Analysis completed in {t_elapsed:.1f}s but identified **0 attack surfaces**. "
                "This may indicate the indexed documents do not describe vehicle interfaces. "
                "Check the knowledge base and re-run, or add more architecture documents."
            )
        else:
            status_box.update(
                label=f"Attack surface analysis complete — {len(surfaces)} surfaces identified.",
                state="complete",
                expanded=False,
            )
            if getattr(llm_client, "is_fallback_active", False) or getattr(llm_client, "is_demo", False):
                reason = getattr(llm_client, "last_fallback_reason", "")
                reason_txt = f" ({reason})" if reason else ""
                st.warning(f"⚠️ **DEMO MODE — PREDEFINED DATA ACTIVE**{reason_txt}: Showing deterministic demonstration attack surfaces.")
            else:
                st.success(
                    f"Attack surface analysis complete in {t_elapsed:.1f}s. "
                    f"Identified **{len(surfaces)} attack surface(s)** for engineering review."
                )

    except RuntimeError as e:
        # Hard failures (empty KB, LLM call failed) — descriptive message
        st.error(f"❌ Attack surface analysis failed: {e}")
    except Exception as e:
        st.error(f"❌ Unexpected error during attack surface analysis: {e}")


# ── Results display ──────────────────────────────────────────────────────────
if 'attack_surfaces' in st.session_state and st.session_state.attack_surfaces:
    surfaces = st.session_state.attack_surfaces
    if getattr(llm_client, "is_fallback_active", False) or getattr(llm_client, "is_demo", False):
        st.info("ℹ️ **Provenance:** Results below are deterministic demonstration candidates, not extracted by live LLM.")
    st.subheader(f"Discovered Attack Surfaces ({len(surfaces)})")
    data = [
        {
            "Interface": s.interface,
            "Connected Component": s.connected_component,
            "Exposure Level": s.exposure,
            "Security Concern": s.security_concern,
        }
        for s in surfaces
    ]
    st.dataframe(pd.DataFrame(data), use_container_width=True)

    st.markdown("### Interface Evidence & Review Status")
    for i, s in enumerate(surfaces):
        with st.expander(f"Surface [{i+1}]: {s.interface} ({s.exposure} exposure)"):
            st.write(f"**Surface ID:** {s.surface_id}")
            st.write(f"**Connected Component:** {s.connected_component}")
            st.write(f"**Security Concern:** {s.security_concern}")
            render_citations(s.evidence)
            new_status = render_review_controls(f"surface_{i}", s.review_status, item_type="attack_surface")
            s.review_status = new_status

elif 'attack_surfaces' in st.session_state and not st.session_state.attack_surfaces:
    # Ran successfully but returned zero — don't show a misleading empty section
    pass
else:
    st.info("Click **'Run Attack Surface Analysis'** above to identify vehicle attack surfaces.")
