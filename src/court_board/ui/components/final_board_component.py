import streamlit as st
import pandas as pd
from ..state import AppState

def render_final_board_page(app_state: AppState):
    st.header("5. Final Board Preview")
    st.markdown("In-app preview of the physical court board layout prior to export.")

    if not app_state.is_processed or not app_state.assembled_board:
        st.info("Please import a file on the Import page first.")
        return

    st.subheader("Physical Board Layout Summary")
    
    sections = app_state.assembled_board.sections
    sec_counts = {s.section_name: len(s.entries) for s in sections}

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### Ready Side")
        st.write(f"- **Hearing:** {sec_counts.get('Hearing', 0)} case(s)")
        st.write(f"- **Part Heard:** {sec_counts.get('Part Heard', 0)} case(s)")
        st.write(f"- **313:** {sec_counts.get('313', 0)} case(s)")
        st.write(f"- **Argument:** {sec_counts.get('Argument', 0)} case(s)")
        st.write(f"- **Judgement:** {sec_counts.get('Judgement', 0)} case(s)")

    with col_b:
        st.markdown("#### Unready Side")
        st.write(f"- **M.A.:** {sec_counts.get('M.A.', 0)} case(s)")
        st.write(f"- **D.V.:** {sec_counts.get('D.V.', 0)} case(s)")
        st.write(f"- **R.C.C. (Merged 2-Col):** {sec_counts.get('R.C.C.', 0)} case(s)")
        st.write(f"- **S.C.C. (Merged 2-Col):** {sec_counts.get('S.C.C.', 0)} case(s)")
        st.write(f"- **N.B.W. / B.W.:** {sec_counts.get('N.B.W. / B.W.', 0)} case(s)")

    st.divider()
    st.subheader("Final Printable Board Simulation (14 Physical Columns)")

    # Build side-by-side grid
    column_headers = [
        "Hearing", "Part Heard", "313", "Argument", "Judgement",
        "[Spacer]", "[Spacer]", "M.A.", "D.V.", "R.C.C.", "(RCC Span)",
        "S.C.C.", "(SCC Span)", "N.B.W. / B.W."
    ]

    col_map = {
        "Hearing": 0, "Part Heard": 1, "313": 2, "Argument": 3, "Judgement": 4,
        "M.A.": 7, "D.V.": 8, "R.C.C.": 9, "S.C.C.": 11, "N.B.W. / B.W.": 13
    }
    
    col_lists = {i: [] for i in range(14)}
    col_lists[5] = ["-"]
    col_lists[6] = ["-"]
    col_lists[10] = ["(Span J-K)"]
    col_lists[12] = ["(Span L-M)"]

    for sec in sections:
        name = sec.section_name.strip()
        if name in col_map:
            idx = col_map[name]
            col_lists[idx] = [e.case_number for e in sec.entries]

    max_rows = max([len(l) for l in col_lists.values()] + [0])

    grid_data = []
    for r in range(max_rows):
        row_dict = {}
        for c_idx, header in enumerate(column_headers):
            cases_in_col = col_lists[c_idx]
            if c_idx in [5, 6, 10, 12]:
                val = cases_in_col[0] if cases_in_col else ""
            else:
                val = cases_in_col[r] if r < len(cases_in_col) else ""
            row_dict[header] = val
        grid_data.append(row_dict)

    df_grid = pd.DataFrame(grid_data)
    st.dataframe(df_grid, use_container_width=True, hide_index=True)
