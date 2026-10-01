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

        table_rows.append({
            "Source Row": r.source_row_index,
            "Case": rec.cases or "",
            "Canonical Stage": r.canonical_stage,
            "Ready / Unready": r.readiness_status,
            "Prefix": r.case_prefix,
            "Destinations": ", ".join(dest_names) if dest_names else "None",
            "Routing Status": r.routing_status,
            "Reason": r.routing_reason
        })

    df = pd.DataFrame(table_rows)
    st.write(f"Showing {len(df)} of {len(app_state.routing_results)} cases:")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Detailed expandable view for individual cases
    st.divider()
    st.subheader("Expandable Case Routing Inspector")
    case_numbers = [r.source_case.cases for r in app_state.routing_results if r.source_case.cases]
    sel_case = st.selectbox("Select Case for Detailed Route Inspection", case_numbers, index=case_numbers.index("R.C.C./300258/1996") if "R.C.C./300258/1996" in case_numbers else 0)

    target_route = next((r for r in app_state.routing_results if r.source_case.cases == sel_case), None)
    if target_route:
        st.markdown(f"### Case: `{target_route.source_case.cases}`")
        st.write(f"**Canonical Stage:** `{target_route.canonical_stage}`")
        st.write(f"**Readiness:** `{target_route.readiness_status}` | **Case Prefix:** `{target_route.case_prefix}`")
        st.write(f"**Status:** `{target_route.routing_status}`")
        st.write(f"**Routing Reason:** {target_route.routing_reason}")

        st.markdown("**Routed Destinations:**")
        if target_route.destinations:
            for d in target_route.destinations:
                st.success(f"✓ Section: **{d.section_name}** | Row: **{d.row_name or 'Section-level'}**")
        else:
            st.error("❌ No valid destinations resolved.")
