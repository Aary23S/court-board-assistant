import streamlit as st
import pandas as pd
from ..state import AppState
from ...routing.prefix_extractor import CasePrefixExtractor

def render_classification_page(app_state: AppState):
    st.header("2. Classification Review")
    st.markdown("Inspect case-by-case stage classification and review unmapped cases.")

    if not app_state.is_processed:
        st.info("Please import a file on the Import page first.")
        return

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Cases", app_state.total_cases)
    m2.metric("Classified", app_state.classified_count)
    m3.metric("Unmapped", app_state.unmapped_count)

    st.subheader("Filter & Search Cases")
    extractor = CasePrefixExtractor()

    # Filters
    col_search, col_stage, col_ready, col_prefix = st.columns(4)
    with col_search:
        search_query = st.text_input("Search (Case / Purpose / Party)", value="")
    with col_stage:
        all_canonical = sorted(list({c.canonical_stage for c in app_state.classification_results if c.canonical_stage}))
        stage_filter = st.selectbox("Canonical Stage", ["All"] + all_canonical)
    with col_ready:
        all_ready = sorted(list({c.source_case.ready_unready_stayed for c in app_state.classification_results if c.source_case.ready_unready_stayed}))
        ready_filter = st.selectbox("Ready / Unready / Stayed", ["All"] + all_ready)
    with col_prefix:
        prefixes = sorted(list({extractor.extract(c.source_case.cases or "") for c in app_state.classification_results}))
        prefix_filter = st.selectbox("Case Prefix", ["All"] + prefixes)

    rows = []
    for c in app_state.classification_results:
        rec = c.source_case
        prefix = extractor.extract(rec.cases or "")
        
        # Apply filters
        if search_query:
            sq = search_query.lower()
            text_pool = f"{rec.cases} {rec.next_purpose} {rec.party_name} {c.canonical_stage}".lower()
            if sq not in text_pool:
                continue

        if stage_filter != "All" and c.canonical_stage != stage_filter:
            continue
        if ready_filter != "All" and rec.ready_unready_stayed != ready_filter:
            continue
        if prefix_filter != "All" and prefix != prefix_filter:
            continue

        rows.append({
            "Row": rec.source_row_index,
            "Case": rec.cases or "",
            "Party Name": rec.party_name or "",
            "Date of Reg.": rec.date_of_registration or "",
            "Ready Status": rec.ready_unready_stayed or "",
            "Next Date": rec.next_date or "",
            "Next Purpose": rec.next_purpose or "",
            "Canonical Stage": c.canonical_stage or "UNMAPPED",
            "Case Prefix": prefix,
            "Classification": c.classification_status
        })

    df = pd.DataFrame(rows)
    st.write(f"Showing {len(df)} of {len(app_state.classification_results)} cases:")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Highlight specific case for verification
    st.divider()
    st.subheader("Single Case Inspector")
    case_numbers = [c.source_case.cases for c in app_state.classification_results if c.source_case.cases]
    selected_case_num = st.selectbox("Select Case to Inspect", case_numbers, index=case_numbers.index("S.C.C./301071/2012") if "S.C.C./301071/2012" in case_numbers else 0)

    target_res = next((c for c in app_state.classification_results if c.source_case.cases == selected_case_num), None)
    if target_res:
        tc = target_res.source_case
        p = extractor.extract(tc.cases or "")
        st.json({
            "Source Row": tc.source_row_index,
            "Case": tc.cases,
            "Next Purpose": tc.next_purpose,
            "Canonical Stage": target_res.canonical_stage,
            "Ready / Unready / Stayed": tc.ready_unready_stayed,
            "Case Prefix": p,
            "Party Name": tc.party_name,
            "Classification Status": target_res.classification_status
        })
