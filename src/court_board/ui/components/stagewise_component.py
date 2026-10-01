import streamlit as st
import pandas as pd
from ..state import AppState

def render_stagewise_page(app_state: AppState):
    st.header("3. Stagewise Visualization")
    st.markdown("View all 49 canonical stages in order and see which cases fall under each stage.")

    if not app_state.is_processed or not app_state.stage_collection:
        st.info("Please import a file on the Import page first.")
        return

    all_stages = app_state.stage_collection.get_all_stages()
    st.write(f"Total Canonical Stages: **{len(all_stages)}**")

    # Filter empty vs populated
    show_empty = st.checkbox("Show empty stages", value=True)

    for stage_config, cases in all_stages:
        case_count = len(cases)
        if not show_empty and case_count == 0:
            continue

        with st.expander(f"Stage {stage_config.order}: **{stage_config.canonical_name}** ({case_count} case(s))", expanded=(case_count > 0)):
            if case_count > 0:
                rows = []
                for res in cases:
                    c = res.source_case
                    rows.append({
                        "Source Row": c.source_row_index,
                        "Case": c.cases or "",
                        "Party Name": c.party_name or "",
                        "Next Purpose": c.next_purpose or "",
                        "Ready / Unready": c.ready_unready_stayed or "",
                        "Next Date": c.next_date or ""
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            else:
                st.caption("No cases classified into this stage.")
