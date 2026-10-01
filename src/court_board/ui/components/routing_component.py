import streamlit as st
import pandas as pd
from ..state import AppState

def render_routing_page(app_state: AppState):
    st.header("4. Routing Review")
    st.markdown("Inspect destination mapping for each case based on canonical stage, prefix, and readiness.")

    if not app_state.is_processed:
        st.info("Please import a file on the Import page first.")
        return

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Cases", app_state.total_cases)
    m2.metric("Routed Cases", app_state.routed_count)
    m3.metric("Unresolved Routing", app_state.unresolved_count)
    m4.metric("Total Destinations", app_state.total_destinations)

    st.subheader("Filter & Review Routing")

    c_section, c_stage, c_status, c_search = st.columns(4)
    with c_section:
        all_sections = set()
        for r in app_state.routing_results:
            for d in r.destinations:
                all_sections.add(d.section_name)
        sec_filter = st.selectbox("Board Section", ["All"] + sorted(list(all_sections)))

    with c_stage:
        all_stages = sorted(list({r.canonical_stage for r in app_state.routing_results if r.canonical_stage}))
        stage_filter = st.selectbox("Canonical Stage ", ["All"] + all_stages)

    with c_status:
        all_statuses = sorted(list({r.routing_status for r in app_state.routing_results if r.routing_status}))
        status_filter = st.selectbox("Routing Status", ["All"] + all_statuses)

    with c_search:
        search_query = st.text_input("Search Case Number", value="")

    table_rows = []
    for r in app_state.routing_results:
        rec = r.source_case
        dest_names = [d.section_name for d in r.destinations]
        
        # Apply filters
        if search_query and search_query.lower() not in (rec.cases or "").lower():
            continue
        if sec_filter != "All" and sec_filter not in dest_names:
            continue
        if stage_filter != "All" and r.canonical_stage != stage_filter:
            continue
        if status_filter != "All" and r.routing_status != status_filter:
            continue

        overrides = getattr(app_state, "manual_stage_overrides", {})
        is_overridden = r.source_row_index in overrides
        status_disp = "OVERRIDDEN" if is_overridden else r.routing_status

        table_rows.append({
            "Source Row": r.source_row_index,
            "Case": rec.cases or "",
            "Canonical Stage": f"⚙️ {r.canonical_stage}" if is_overridden else r.canonical_stage,
            "Ready / Unready": r.readiness_status,
            "Prefix": r.case_prefix,
            "Destinations": ", ".join(dest_names) if dest_names else "None",
            "Routing Status": status_disp,
            "Reason": r.routing_reason
        })

    df = pd.DataFrame(table_rows)
    st.write(f"Showing {len(df)} of {len(app_state.routing_results)} cases:")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Manual Stage Override Controls
    st.divider()
    st.subheader("✏️ Manual Stage Selection & Case Correction")
    st.markdown("If a case was incorrectly categorized, select the case below to manually assign a different canonical stage. The routing engine and final board will immediately re-calculate.")

    case_options = {f"{r.source_case.cases} (Row {r.source_row_index})": r for r in app_state.routing_results if r.source_case.cases}
    selected_label = st.selectbox("Select Case to Correct", list(case_options.keys()))

    if selected_label:
        selected_route = case_options[selected_label]
        case_rec = selected_route.source_case
        row_idx = case_rec.source_row_index

        all_canonical_stages = [s.canonical_name for s in app_state.classification_engine.get_stages()]
        current_canonical = selected_route.canonical_stage

        c1, c2 = st.columns(2)
        with c1:
            st.info(f"**Case Number:** `{case_rec.cases}`\n\n"
                    f"**Next Purpose (Source):** `{case_rec.next_purpose}`\n\n"
                    f"**Current Canonical Stage:** `{current_canonical}`\n\n"
                    f"**Readiness:** `{selected_route.readiness_status}` | **Prefix:** `{selected_route.case_prefix}`")

        with c2:
            st.markdown("#### Assign New Stage")
            default_index = all_canonical_stages.index(current_canonical) if current_canonical in all_canonical_stages else 0
            new_stage = st.selectbox("Select Correct Canonical Stage", all_canonical_stages, index=default_index, key="manual_stage_select")

            b_col1, b_col2 = st.columns(2)
            with b_col1:
                if st.button("Apply Stage Change", type="primary"):
                    app_state.override_case_stage(row_idx, new_stage)
                    st.success(f"Updated `{case_rec.cases}` stage to **{new_stage}**!")
                    st.rerun()
            with b_col2:
                if row_idx in getattr(app_state, "manual_stage_overrides", {}):
                    if st.button("Reset to Original Stage"):
                        app_state.reset_case_stage_override(row_idx)
                        st.info(f"Reset `{case_rec.cases}` to original classification.")
                        st.rerun()

    active_overrides = getattr(app_state, "manual_stage_overrides", {})
    if active_overrides:
        st.caption(f"Active manual stage corrections: **{len(active_overrides)}** case(s).")
