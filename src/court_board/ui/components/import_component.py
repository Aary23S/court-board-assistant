import streamlit as st
import tempfile
from pathlib import Path
from ..state import AppState

def render_import_page(app_state: AppState):
    st.header("1. Source File Import & Pipeline Analysis")
    st.markdown("Upload a daily court case workbook (`.xlsx` or `.ods`) or load the sample file.")

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader("Upload Source File", type=["xlsx", "ods"])
        if uploaded_file is not None:
            if st.button("Import & Analyze Uploaded File", type="primary"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
                    tmp.write(uploaded_file.getbuffer())
                    tmp_path = tmp.name
                with st.spinner("Processing pipeline..."):
                    app_state.process_file(tmp_path, filename=uploaded_file.name)
                st.success(f"Successfully processed `{uploaded_file.name}`!")

    with col2:
        st.subheader("Sample File")
        default_sample = "samples/01.07.2026.xlsx"
        if Path(default_sample).exists():
            st.info("Quick load sample `01.07.2026.xlsx`")
            if st.button("Load Sample File"):
                with st.spinner("Processing sample pipeline..."):
                    app_state.process_file(default_sample, filename="01.07.2026.xlsx")
                st.success("Sample file loaded successfully!")

    st.divider()

    if app_state.is_processed:
        st.subheader("Live Pipeline Summary Metrics")
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Source Cases", app_state.total_cases)
        m2.metric("Classified", app_state.classified_count)
        m3.metric("Unmapped", app_state.unmapped_count)
        m4.metric("Routed Cases", app_state.routed_count)
        m5.metric("Unresolved", app_state.unresolved_count)
        m6.metric("Total Destinations", app_state.total_destinations)

        if app_state.unresolved_count > 0:
            st.warning(f"⚠️ {app_state.unresolved_count} case(s) require review (unresolved routing or unmapped stage).")
        else:
            st.success("✓ Pipeline executed cleanly with 0 unresolved cases.")
    else:
        st.info("Please upload a file or load the sample file to begin.")
