"""
Streamlit UI Component for Roznama PDF Generator (Phase 5A).
Handles PDF upload, document analysis, human-in-the-loop review, and validation gate.
"""
import streamlit as st
import tempfile
from pathlib import Path

from court_board.roznama.ui.roznama_state import RoznamaState
from court_board.roznama.transformation.transformer import RoznamaTransformer

def render_roznama_page(roznama_state: RoznamaState):
    st.header("📄 Roznama PDF Generator")
    st.caption("न्यायालयीन कामकाजाचा दैनंदिन रोजनामा तयार करणे (Lohit Marathi PDF Generation)")

    # -------------------------------------------------------------
    # Step 1: Upload Source PDF
    # -------------------------------------------------------------
    st.subheader("१. मूळ कामकाज PDF अपलोड करा (Upload Source PDF)")

    col_up, col_info = st.columns([2, 1])
    with col_up:
        uploaded_file = st.file_uploader(
            "Select Proceedings PDF (न्यायालयीन कामकाजाची PDF निवडा)",
            type=["pdf"],
            key="roznama_pdf_uploader",
            help="Supports native text PDFs from e-Courts / CIS."
        )

    with col_info:
        if roznama_state.is_extracted:
            st.success(f"**Loaded:** `{roznama_state.source_filename}`")
            if st.button("🔄 Clear / Start New (नवीन दस्तऐवज)", use_container_width=True):
                roznama_state.reset()
                st.rerun()

    # Process file when uploaded and not yet extracted
    if uploaded_file is not None and (
        not roznama_state.is_extracted or roznama_state.source_filename != uploaded_file.name
    ):
        file_bytes = uploaded_file.read()
        with tempfile.NamedTemporaryFile("wb", suffix=".pdf", delete=False) as tf:
            tf.write(file_bytes)
            tmp_pdf_path = tf.name

        with st.spinner("Extracting and analyzing PDF pages... (कामकाज तपशील वाचत आहे...)"):
            roznama_state.process_pdf(tmp_pdf_path, filename=uploaded_file.name, file_bytes=file_bytes)
            Path(tmp_pdf_path).unlink(missing_ok=True)
            st.rerun()

    if not roznama_state.is_extracted:
        st.info("👆 Please upload a court proceedings PDF above to begin.")
        return

    # -------------------------------------------------------------
    # Step 2: Document Analysis & Extraction Status
    # -------------------------------------------------------------
    st.divider()
    st.subheader("२. दस्तऐवज विश्लेषण (Document Analysis)")

    summary = roznama_state.document_summary
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Pages (एकूण पृष्ठे)", summary.total_pages if summary else 0)
    with c2:
        st.metric("Total Records (एकूण नोंदी)", len(roznama_state.transformed_records))
    with c3:
        st.metric("Method (पद्धत)", summary.overall_method if summary else "N/A")
    with c4:
        st.metric("Quality (गुणवत्ता)", summary.overall_quality if summary else "N/A")

    if summary and summary.pages_requiring_ocr:
        ocr_ack_key = "ocr_pages_acknowledgement"
        st.warning(
            f"⚠️ Pages {summary.pages_requiring_ocr} have sparse/missing text layer and required OCR."
        )
        ack_ocr = st.checkbox(
            f"Acknowledge OCR/uncertain text quality on pages {summary.pages_requiring_ocr} and confirm review",
            value=(ocr_ack_key in roznama_state.acknowledged_warnings),
            key="ack_ocr_pages"
        )
        if ack_ocr:
            roznama_state.acknowledge_warning(ocr_ack_key)
        else:
            roznama_state.unacknowledge_warning(ocr_ack_key)

    # -------------------------------------------------------------
    # Step 3 & 4: Human Review & Corrections
    # -------------------------------------------------------------
    st.divider()
    st.subheader("३. नोंदींचे पुनरावलोकन व दुरुस्ती (Human-in-the-Loop Review)")
    st.markdown(
        "कागदपत्रातील माहिती तपासा. गरज भासल्यास **दिनांक, कामकाज, किंवा स्टेज** दुरुस्त करा. "
        "दुरुस्तीनंतर कामकाज तपशील आपोआप योग्य स्वरूपात तयार होईल."
    )

    # Review Progress Bar
    total_recs = len(roznama_state.transformed_records)
    reviewed_count = len(roznama_state.reviewed_sequences)
    progress_val = (reviewed_count / total_recs) if total_recs > 0 else 0.0

    p_col, b_col = st.columns([3, 1])
    with p_col:
        st.progress(progress_val, text=f"Reviewed {reviewed_count} of {total_recs} records ({int(progress_val*100)}%)")
    with b_col:
        if st.button("✅ Mark All as Reviewed", use_container_width=True):
            roznama_state.mark_all_reviewed()
            st.rerun()

    # Filter / Search / Select Record for Editing
    st.markdown("#### Record Editor (नोंद संपादन)")
    selected_seq = st.selectbox(
        "Select Record to Inspect / Edit (नोंद निवडा):",
        options=[r.record_sequence for r in roznama_state.transformed_records],
        format_func=lambda s: (
            f"Record #{s} — {next(r.today_date for r in roznama_state.transformed_records if r.record_sequence == s)} "
            f"({'🛑 Category C Review' if (s in roznama_state.category_c_events and any(e['event_id'] not in roznama_state.approved_category_c_events.get(s, set()) for e in roznama_state.category_c_events[s])) else ('⚠️ मजकूर तपासणी' if s in roznama_state.flagged_fidelity_records else ('✅ Reviewed' if s in roznama_state.reviewed_sequences else '⏳ Pending'))})"
        )
    )

    if selected_seq:
        rec = next(r for r in roznama_state.transformed_records if r.record_sequence == selected_seq)
        source_rec = next((s for s in roznama_state.original_source_records if s.record_sequence == selected_seq), None)

        edits = roznama_state.human_edits.get(selected_seq, {})
        current_b = edits.get("business", source_rec.business if source_rec else "")
        current_s = edits.get("stage", source_rec.stage if source_rec else "")
        current_d = edits.get("date", rec.today_date)
        current_next_d = rec.next_date or ""
        original_derived_next = roznama_state.original_derived_next_dates.get(selected_seq) or "---"

        # Display fidelity warning if flagged
        if selected_seq in roznama_state.flagged_fidelity_records:
            st.warning(
                f"⚠️ **मराठी मजकूर तपासणी सूचना (Fidelity Notice for Record #{selected_seq}):** "
                + "; ".join(roznama_state.flagged_fidelity_records[selected_seq])
            )

        # Display Category C Discretionary Review if present
        if selected_seq in roznama_state.category_c_events:
            cat_c_list = roznama_state.category_c_events[selected_seq]
            approved_set = roznama_state.approved_category_c_events.get(selected_seq, set())
            for ev in cat_c_list:
                ev_id = ev["event_id"]
                is_appr = ev_id in approved_set
                with st.expander(
                    f"{'✅ Approved' if is_appr else '🛑 Action Required'}: {ev['title']} (Page {ev['page']})",
                    expanded=(not is_appr)
                ):
                    st.markdown(f"**Context:** `{ev['raw_context']}`")
                    st.markdown(f"**Reason:** {ev['reason']}")
                    st.markdown(f"**Proposed Text:** `{ev['proposed_correction']}`")

                    c_act1, c_act2 = st.columns([1, 1])
                    with c_act1:
                        if not is_appr:
                            if st.button(f"✅ Accept Proposal ({ev['proposed_correction']})", key=f"appr_{ev_id}", use_container_width=True):
                                roznama_state.approve_category_c_event(selected_seq, ev_id)
                                st.rerun()
                        else:
                            st.success("Proposal approved by operator.")
                    with c_act2:
                        if st.button(f"↩️ Reject Proposal (Retain Original)", key=f"rej_{ev_id}", use_container_width=True):
                            roznama_state.reject_category_c_event(selected_seq, ev_id, ev["raw_context"].split(" -> ")[0])
                            st.rerun()

        with st.container(border=True):
            meta_c1, meta_c2, meta_c3, meta_c4 = st.columns(4)
            with meta_c1:
                st.caption(f"**Original SN:** `{source_rec.serial_number if source_rec else 'N/A'}`")
            with meta_c2:
                st.caption(f"**Source Page:** `{source_rec.source_page_start if source_rec else 'N/A'}`")
            with meta_c3:
                st.caption(f"**Case No:** `{source_rec.case_number if source_rec else 'N/A'}`")
            with meta_c4:
                st.caption(f"**Original Derived Next Date:** `{original_derived_next}`")

            edit_c1, edit_c2 = st.columns([1, 1])
            with edit_c1:
                new_date = st.text_input("आजची दिनांक (Today's Date):", value=current_d, key=f"date_{selected_seq}")
                new_stage = st.text_input("स्टेज (Stage):", value=current_s, key=f"stage_{selected_seq}")
                manual_next = st.text_input(
                    "पुढे/निकाल तारीख (Next Date - Override):",
                    value=current_next_d,
                    key=f"next_{selected_seq}",
                    help="Default is derived automatically from the next record. Enter a date to manually override."
                )

            with edit_c2:
                new_business = st.text_area("कामकाज तपशील (Business Description):", value=current_b, height=120, key=f"bus_{selected_seq}")

            # Live preview computed using the public RoznamaTransformer API
            preview_detail = RoznamaTransformer.format_proceedings_detail(new_business, new_stage)
            st.markdown(f"**Preview of Combined Cell (Col 2 Output):**")
            st.info(preview_detail if preview_detail else "*(काहीही नाही — Empty)*")

            # Acknowledgement for missing business or stage
            if not new_business.strip() or not new_stage.strip():
                warn_k = f"empty_field_rec_{selected_seq}"
                ack = st.checkbox(
                    f"⚠️ Confirm and acknowledge: {'Business' if not new_business.strip() else 'Stage'} is intentionally empty for Record #{selected_seq}",
                    value=(warn_k in roznama_state.acknowledged_warnings),
                    key=f"ack_{selected_seq}"
                )
                if ack:
                    roznama_state.acknowledge_warning(warn_k)
                else:
                    roznama_state.unacknowledge_warning(warn_k)

            save_col, review_col = st.columns([1, 1])
            with save_col:
                if st.button("💾 Save Changes (बदल जतन करा)", key=f"save_{selected_seq}", use_container_width=True):
                    roznama_state.update_record(
                        record_sequence=selected_seq,
                        new_date=new_date,
                        new_business=new_business,
                        new_stage=new_stage,
                        manual_next_date=manual_next
                    )
                    st.success("Record updated successfully!")
                    st.rerun()

            with review_col:
                is_rev = selected_seq in roznama_state.reviewed_sequences
                btn_label = "✅ Record is Reviewed" if is_rev else "Mark as Reviewed (तपासले म्हणून खूण करा)"
                if st.button(btn_label, key=f"mark_{selected_seq}", use_container_width=True):
                    roznama_state.mark_reviewed(selected_seq)
                    st.rerun()

    # Full Records Overview Table
    st.markdown("#### सर्व नोंदींचा गोषवारा (All Proceedings Records)")
    table_data = []
    for r in roznama_state.transformed_records:
        source_r = next((s for s in roznama_state.source_records if s.record_sequence == r.record_sequence), None)
        status_label = "✅ Reviewed" if r.record_sequence in roznama_state.reviewed_sequences else "⏳ Pending"
        if r.record_sequence in roznama_state.flagged_fidelity_records:
            status_label = "⚠️ मजकूर तपासणी"
        if (r.record_sequence in roznama_state.category_c_events and
            any(e['event_id'] not in roznama_state.approved_category_c_events.get(r.record_sequence, set())
                for e in roznama_state.category_c_events[r.record_sequence])):
            status_label = "🛑 Category C Review"

        table_data.append({
            "Seq": r.record_sequence,
            "Orig SN": source_r.serial_number if source_r else "",
            "आजची दिनांक": r.today_date,
            "दैनंदिन कामकाज तपशील": r.proceedings_detail,
            "पुढे/निकाल तारीख": r.next_date or "---",
            "Status": status_label
        })
    st.dataframe(table_data, use_container_width=True, hide_index=True)

    # -------------------------------------------------------------
    # Step 5: Validation Gate & Generation Eligibility
    # -------------------------------------------------------------
    st.divider()
    st.subheader("४. तपासणी व मंजुरी (Validation Gate & Eligibility)")

    is_valid = roznama_state.validate()

    # Display Status Metrics
    total_src = len(roznama_state.original_source_records)
    total_rev = len(roznama_state.reviewed_sequences)
    total_corr = len(roznama_state.human_edits) + len(roznama_state.next_date_overrides)
    total_acks = len(roznama_state.acknowledged_warnings)

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Source Records", total_src)
    with m2:
        st.metric("Reviewed Records", f"{total_rev}/{total_src}")
    with m3:
        st.metric("Corrected Records", total_corr)
    with m4:
        st.metric("Acknowledged", total_acks)
    with m5:
        if is_valid and not roznama_state.validation_warnings:
            st.metric("Status", "✅ Ready")
        elif not is_valid:
            st.metric("Status", "❌ Blocking Errors")
        else:
            st.metric("Status", "⚠️ Warnings Pending")

    if roznama_state.validation_errors:
        st.error("❌ **Validation Errors Found (खालील त्रुटी दूर करा):**")
        for err in roznama_state.validation_errors:
            st.write(f"- {err}")

    if roznama_state.validation_warnings:
        st.warning("⚠️ **Review Warnings (कृती आवश्यक):**")
        for warn in roznama_state.validation_warnings:
            st.write(f"- {warn}")

    eligible = roznama_state.is_generation_eligible()

    if eligible:
        st.success("✅ **Eligibility Gate Passed:** Records are fully reviewed, validated, and ready for PDF generation.")
    else:
        st.info("ℹ️ Complete review of all records and acknowledge any warnings above to enable PDF generation.")

    # -------------------------------------------------------------
    # Step 6: PDF Generation, Preview & Download (Phase 5B)
    # -------------------------------------------------------------
    st.divider()
    st.subheader("५. रोजनामा PDF निर्मिती व डाऊनलोड (Generate, Preview & Download)")

    gen_col1, gen_col2 = st.columns([2, 1])

    with gen_col1:
        gen_button_label = "⚡ Generate Final Roznama PDF (रोजनामा तयार करा)"
        if roznama_state.generated_pdf_bytes:
            gen_button_label = "🔄 Regenerate PDF (रोजनामा पुन्हा तयार करा)"

        if st.button(
            gen_button_label,
            disabled=not eligible,
            type="primary",
            use_container_width=True,
            key="btn_generate_roznama_pdf"
        ):
            with st.spinner("Generating official Roznama PDF with Lohit Marathi font... (PDF तयार करत आहे...)"):
                success = roznama_state.generate_pdf()
                if success:
                    st.success("🎉 Roznama PDF generated successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to generate PDF: {roznama_state.generation_error}")

    with gen_col2:
        if roznama_state.generated_pdf_bytes:
            st.download_button(
                label=f"📥 Download {roznama_state.generated_pdf_filename}",
                data=roznama_state.generated_pdf_bytes,
                file_name=roznama_state.generated_pdf_filename,
                mime="application/pdf",
                type="primary",
                use_container_width=True,
                key="btn_download_roznama_pdf"
            )

    # Preview Area
    if roznama_state.generated_pdf_bytes and roznama_state.generated_pdf_path:
        with st.container(border=True):
            st.markdown("### 📄 Generated PDF Details & Preview")
            inf1, inf2, inf3, inf4 = st.columns(4)
            with inf1:
                st.caption(f"**Filename:** `{roznama_state.generated_pdf_filename}`")
            with inf2:
                st.caption(f"**Total Pages:** `{roznama_state.generated_page_count}`")
            with inf3:
                st.caption(f"**Proceedings Count:** `{roznama_state.generated_record_count}`")
            with inf4:
                st.caption(f"**Generated At:** `{roznama_state.generated_timestamp}`")

            # Inline PDF Preview via iframe
            import base64
            pdf_b64 = base64.b64encode(roznama_state.generated_pdf_bytes).decode("ascii")
            pdf_display = f'<iframe src="data:application/pdf;base64,{pdf_b64}" width="100%" height="700" type="application/pdf" style="border: 1px solid #ddd; border-radius: 4px;"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)

