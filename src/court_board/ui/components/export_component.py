import streamlit as st
import tempfile
from pathlib import Path
from ..state import AppState

def render_export_page(app_state: AppState):
    st.header("6. Validation Gate & Export")
    st.markdown("Validate all stage & routing invariants before exporting printable ODS and PDF documents.")

    if not app_state.is_processed:
        st.info("Please import a file on the Import page first.")
        return

    st.subheader("Validation Gate")

    # Run check gate
    checks = []
    
    # 1. Source check
    checks.append(("Source imported", app_state.total_cases > 0, f"{app_state.total_cases} cases loaded"))
    
    # 2. Classification check
    class_pass = (app_state.classified_count == app_state.total_cases)
    checks.append(("Cases classified", class_pass, f"{app_state.classified_count}/{app_state.total_cases} classified"))
    
    # 3. Routing check
    route_pass = (app_state.routed_count == app_state.total_cases)
    checks.append(("Routing completed", route_pass, f"{app_state.routed_count}/{app_state.total_cases} routed"))
    
    # 4. Destinations check
    checks.append(("Destinations accounted for", app_state.total_destinations > 0, f"{app_state.total_destinations} destinations"))

    # 5. Validation report check
    if app_state.validation_report:
        checks.append(("Final board entries accounted for", app_state.validation_report.entries_count_pass, f"{app_state.validation_report.actual_final_board_entries} entries"))
        checks.append(("Required sections present", app_state.validation_report.all_sections_present, "All 10 template sections present"))
        checks.append(("No unexpected entries", app_state.validation_report.no_unexpected_entries, "0 unexpected entries"))

    all_passed = all(c[1] for c in checks)

    for title, status, info in checks:
        if status:
            st.success(f"✓ **{title}**: {info}")
        else:
            st.error(f"❌ **{title}**: {info}")

    st.divider()

    if not all_passed:
        st.error("❌ **Export Blocked**: One or more validation gate checks failed.")
        return

    st.success("✓ **Validation Gate Passed**: All checks green. Output files are ready for export.")

    st.subheader("Export Options")

    col1, col2, col3 = st.columns(3)

    board_date = "01.07.2026"
    if app_state.cases and app_state.cases[0].next_date:
        board_date = app_state.cases[0].next_date.replace("/", ".").replace("-", ".")

    with col1:
        st.markdown("#### 1. Stagewise Review ODS")
        st.caption("Contains Stagewise, Case Classification, and Routing Review sheets.")
        if st.button("Generate Stagewise ODS"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ods") as tmp:
                out_path = tmp.name
            app_state.generate_stagewise_ods(out_path)
            with open(out_path, "rb") as f:
                st.download_button(
                    label="Download Stagewise ODS",
                    data=f.read(),
                    file_name=f"{board_date}_stagewise_review.ods",
                    mime="application/vnd.oasis.opendocument.spreadsheet"
                )

    with col2:
        st.markdown("#### 2. Final Board ODS")
        st.caption("Printable daily court board ODS with exact 14 physical columns.")
        if st.button("Generate Final Board ODS"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ods") as tmp:
                out_path = tmp.name
            app_state.generate_final_board_ods(out_path)
            with open(out_path, "rb") as f:
                st.download_button(
                    label="Download Final Board ODS",
                    data=f.read(),
                    file_name=f"{board_date}_final_board.ods",
                    mime="application/vnd.oasis.opendocument.spreadsheet"
                )

    with col3:
        st.markdown("#### 3. PDF Document")
        st.caption("Print-ready PDF export via LibreOffice Calc.")
        if app_state.is_libreoffice_available():
            if st.button("Generate PDF"):
                with tempfile.TemporaryDirectory() as tmpdir:
                    ods_file = str(Path(tmpdir) / f"{board_date}_final_board.ods")
                    app_state.generate_final_board_ods(ods_file)
                    pdf_path = app_state.generate_pdf(ods_file, tmpdir)
                    if pdf_path and Path(pdf_path).exists():
                        with open(pdf_path, "rb") as f:
                            st.download_button(
                                label="Download Final Board PDF",
                                data=f.read(),
                                file_name=f"{board_date}_final_board.pdf",
                                mime="application/pdf"
                            )
                    else:
                        st.error("Failed to generate PDF with LibreOffice.")
        else:
            st.info("ℹ️ LibreOffice is not installed/available on this system.\nThe Final Board ODS is ready.")
