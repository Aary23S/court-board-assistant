"""
Unit and integration tests for Phase 5A: Roznama Streamlit State & Workflow.
Verifies state isolation, review tracking, edit propagation, and validation gate.
"""
import pytest
from pathlib import Path

from court_board.roznama.ui.roznama_state import RoznamaState
from court_board.ui.state import AppState

SAMPLE_DIR = Path("samples/roznama/source")

class TestRoznamaState:
    @pytest.fixture
    def state(self):
        return RoznamaState()

    def test_state_isolation_from_court_board(self, state):
        court_board_state = AppState()
        
        # Modify Court Board state
        court_board_state.manual_stage_overrides[5] = "Arguments"
        
        # Roznama state must remain empty and independent
        assert len(state.source_records) == 0
        assert len(state.human_edits) == 0
        assert len(state.next_date_overrides) == 0

    def test_process_pdf_and_invariants(self, state):
        f = SAMPLE_DIR / "D.V. 260 of 2024.pdf"
        if not f.exists():
            pytest.skip("Sample PDF not found")

        state.process_pdf(str(f), filename="D.V. 260 of 2024.pdf")

        assert state.is_extracted is True
        assert len(state.source_records) == 36
        assert len(state.transformed_records) == 36
        assert state.document_summary is not None
        assert state.document_summary.total_pages == 9

        # Invariant check
        assert state.transformed_records[0].today_date == "30-05-2024"
        assert state.transformed_records[0].next_date == "20-06-2024"
        assert state.transformed_records[-1].next_date is None

    def test_human_edits_regenerates_proceedings_detail(self, state):
        f = SAMPLE_DIR / "D.V. 260 of 2024.pdf"
        if not f.exists():
            pytest.skip("Sample PDF not found")

        state.process_pdf(str(f), filename="D.V. 260 of 2024.pdf")

        # Edit record 1
        state.update_record(
            record_sequence=1,
            new_business="नवीन कामकाज तपशील नोंदविला",
            new_stage="अंतिम सुनावणी"
        )

        rec1 = state.transformed_records[0]
        assert rec1.record_sequence == 1
        assert "नवीन कामकाज तपशील नोंदविला. Stage: अंतिम सुनावणी" == rec1.proceedings_detail
        assert 1 in state.reviewed_sequences

    def test_manual_next_date_override(self, state):
        f = SAMPLE_DIR / "D.V. 260 of 2024.pdf"
        if not f.exists():
            pytest.skip("Sample PDF not found")

        state.process_pdf(str(f), filename="D.V. 260 of 2024.pdf")

        # Manually override next date for record 1
        state.update_record(
            record_sequence=1,
            manual_next_date="25-06-2024"
        )

        assert state.transformed_records[0].next_date == "25-06-2024"
        assert state.next_date_overrides[1] == "25-06-2024"

    def test_validation_gate(self, state):
        f = SAMPLE_DIR / "D.V. 260 of 2024.pdf"
        if not f.exists():
            pytest.skip("Sample PDF not found")

        state.process_pdf(str(f))

        # Initial validation has warnings because records are unreviewed
        assert state.validate() is True
        assert any("have not been marked as reviewed" in w for w in state.validation_warnings)

        # Mark all reviewed
        state.mark_all_reviewed()
        assert len(state.reviewed_sequences) == 36
        assert state.validate() is True
        assert not any("have not been marked as reviewed" in w for w in state.validation_warnings)

    def test_reset_on_new_file(self, state):
        f = SAMPLE_DIR / "D.V. 260 of 2024.pdf"
        if not f.exists():
            pytest.skip("Sample PDF not found")

        state.process_pdf(str(f))
        assert state.is_extracted is True

        state.reset()
        assert state.is_extracted is False
        assert len(state.source_records) == 0
        assert len(state.transformed_records) == 0
        assert len(state.reviewed_sequences) == 0

    def test_original_source_records_immutable_on_human_edit(self, state):
        """Verifies that user modifications in RoznamaState never mutate original extracted records."""
        f = SAMPLE_DIR / "D.V. 260 of 2024.pdf"
        if not f.exists():
            pytest.skip("Sample PDF not found")

        state.process_pdf(str(f))
        orig_rec_1_business = state.original_source_records[0].business
        orig_rec_1_date = state.original_source_records[0].hearing_date

        state.update_record(
            record_sequence=1,
            new_date="01-01-2025",
            new_business="Modified Business Note",
            new_stage="Arguments",
            manual_next_date="15-01-2025"
        )

        # Original source record must remain completely untouched
        assert state.original_source_records[0].business == orig_rec_1_business
        assert state.original_source_records[0].hearing_date == orig_rec_1_date
        assert state.source_records[0].business == orig_rec_1_business

        # Human edit and transformed records should have new values
        assert state.human_edits[1]["business"] == "Modified Business Note"
        assert state.transformed_records[0].today_date == "01-01-2025"
        assert state.transformed_records[0].next_date == "15-01-2025"
        # Original derived date is preserved in history
        assert state.original_derived_next_dates[1] == "20-06-2024"

    def test_calendar_date_validation(self, state):
        """Verifies strict calendar date validation (DD-MM-YYYY, real days and months)."""
        assert RoznamaState.is_valid_calendar_date("29-02-2024") is True   # Leap year
        assert RoznamaState.is_valid_calendar_date("29-02-2023") is False  # Non-leap year
        assert RoznamaState.is_valid_calendar_date("31-04-2024") is False  # April has 30 days
        assert RoznamaState.is_valid_calendar_date("32-01-2024") is False  # Invalid day
        assert RoznamaState.is_valid_calendar_date("15-13-2024") is False  # Invalid month
        assert RoznamaState.is_valid_calendar_date("2024-05-30") is False  # Incorrect format

    def test_record_count_and_sequence_validation(self, state):
        """Verifies error detection for record count and sequence discontinuities."""
        f = SAMPLE_DIR / "D.V. 260 of 2024.pdf"
        if not f.exists():
            pytest.skip("Sample PDF not found")

        state.process_pdf(str(f))
        assert state.validate() is True

        # Simulate transformed record removal
        popped = state.transformed_records.pop()
        assert state.validate() is False
        assert any("Record count mismatch" in err for err in state.validation_errors)

        # Restore
        state.transformed_records.append(popped)
        assert state.validate() is True

    def test_warning_acknowledgement_flow(self, state):
        """Verifies acknowledgement tracking for empty fields or uncertain OCR pages."""
        f = SAMPLE_DIR / "D.V. 260 of 2024.pdf"
        if not f.exists():
            pytest.skip("Sample PDF not found")

        state.process_pdf(str(f))
        state.mark_all_reviewed()

        # Artificially clear stage on record 2
        state.update_record(record_sequence=2, new_stage="")
        assert state.validate() is True
        assert any("empty_field_rec_2" in w or "Stage" in w for w in state.validation_warnings)

        # Acknowledge
        state.acknowledge_warning("empty_field_rec_2")
        state.validate()
        assert not any("empty_field_rec_2" in w or "Stage (स्टेज) is empty" in w for w in state.validation_warnings)

    def test_validation_calendar_dates_and_overrides(self, state):
        """Covers invalid calendar dates like 31-02-2026, valid date corrections, and invalid next-date overrides."""
        f = SAMPLE_DIR / "D.V. 260 of 2024.pdf"
        if not f.exists():
            pytest.skip("Sample PDF not found")

        state.process_pdf(str(f))
        state.mark_all_reviewed()

        # 1. Invalid calendar date 31-02-2026 in today_date
        state.update_record(record_sequence=1, new_date="31-02-2026")
        assert state.validate() is False
        assert any("Record #1: Invalid calendar date '31-02-2026'" in err for err in state.validation_errors)

        # 2. Valid date correction
        state.update_record(record_sequence=1, new_date="15-06-2024")
        assert state.validate() is True

        # 3. Invalid next-date override
        state.update_record(record_sequence=1, manual_next_date="31-04-2024")  # April has only 30 days
        assert state.validate() is False
        assert any("Record #1: Invalid next date '31-04-2024'" in err for err in state.validation_errors)

        # 4. Valid next-date override restore
        state.update_record(record_sequence=1, manual_next_date="30-04-2024")
        assert state.validate() is True

    def test_validation_sequence_integrity_and_duplicates(self, state):
        """Covers duplicate sequences, missing sequences, and sequence ordering changes."""
        f = SAMPLE_DIR / "D.V. 260 of 2024.pdf"
        if not f.exists():
            pytest.skip("Sample PDF not found")

        state.process_pdf(str(f))
        state.mark_all_reviewed()

        # Duplicate sequence
        original_seq = state.transformed_records[1].record_sequence
        state.transformed_records[1].record_sequence = 1
        assert state.validate() is False
        assert any("Duplicate record sequence numbers detected" in err for err in state.validation_errors)

        # Sequence ordering change / discontinuity
        state.transformed_records[1].record_sequence = original_seq
        # Swap sequences 1 and 2
        state.transformed_records[0].record_sequence = 2
        state.transformed_records[1].record_sequence = 1
        assert state.validate() is False
        assert any("Record sequences are not continuous from 1 to N" in err for err in state.validation_errors)

        # Restore
        state.transformed_records[0].record_sequence = 1
        state.transformed_records[1].record_sequence = 2
        assert state.validate() is True

    def test_ocr_uncertainty_acknowledgement(self, state):
        """Covers unresolved extraction errors / uncertainty acknowledgement from document summary."""
        f = SAMPLE_DIR / "D.V. 260 of 2024.pdf"
        if not f.exists():
            pytest.skip("Sample PDF not found")

        state.process_pdf(str(f))
        state.mark_all_reviewed()

        # Artificially simulate OCR required on pages
        state.document_summary.pages_requiring_ocr = [2, 5]
        assert state.validate() is True
        assert any("Pages [2, 5] required OCR / have uncertain quality" in w for w in state.validation_warnings)

        # Acknowledge
        state.acknowledge_warning("ocr_pages_acknowledgement")
        state.validate()
        assert not any("Pages [2, 5] required OCR" in w for w in state.validation_warnings)

    def test_streamlit_interaction_workflow_simulation(self, state):
        """
        Simulates the entire Streamlit interaction sequence:
        1. Upload & extraction
        2. Business editing
        3. Stage editing
        4. Saving corrections
        5. Next-date manual override
        6. Source replacement and state reset
        7. Switching application mode while preserving independent state
        """
        f = SAMPLE_DIR / "D.V. 260 of 2024.pdf"
        if not f.exists():
            pytest.skip("Sample PDF not found")

        # Step 1: Upload & Extraction
        state.process_pdf(str(f), filename="D.V. 260 of 2024.pdf")
        assert state.is_extracted is True
        assert len(state.source_records) == 36
        assert len(state.transformed_records) == 36

        # Step 2 & 3: Business editing & Stage editing
        orig_business = state.original_source_records[0].business
        orig_stage = state.original_source_records[0].stage
        orig_derived_next = state.original_derived_next_dates[1]

        # Step 4: Saving corrections
        state.update_record(
            record_sequence=1,
            new_business="सुनावणी पूर्ण झाली व निकाल राखून ठेवला",
            new_stage="निकाल"
        )
        assert state.original_source_records[0].business == orig_business
        assert state.original_source_records[0].stage == orig_stage
        assert state.human_edits[1]["business"] == "सुनावणी पूर्ण झाली व निकाल राखून ठेवला"
        assert state.human_edits[1]["stage"] == "निकाल"
        assert state.transformed_records[0].proceedings_detail == "सुनावणी पूर्ण झाली व निकाल राखून ठेवला. Stage: निकाल"

        # Step 5: Next-date override
        state.update_record(
            record_sequence=1,
            manual_next_date="15-07-2024"
        )
        assert state.transformed_records[0].next_date == "15-07-2024"
        assert state.next_date_overrides[1] == "15-07-2024"
        assert state.original_derived_next_dates[1] == orig_derived_next

        # Step 6: Switching application mode while preserving independent state
        court_board_state = AppState()
        court_board_state.manual_stage_overrides[10] = "Evidence"

        # Verify independence
        assert 10 not in state.human_edits
        assert 10 not in state.next_date_overrides
        assert state.transformed_records[0].next_date == "15-07-2024"

        # Step 7: Source replacement and state reset
        f2 = SAMPLE_DIR / "M.A.919 of 2020.pdf"
        if f2.exists():
            state.process_pdf(str(f2), filename="M.A.919 of 2020.pdf")
            assert state.source_filename == "M.A.919 of 2020.pdf"
            assert len(state.source_records) == 67
            assert len(state.transformed_records) == 67
            assert len(state.human_edits) == 0  # Prior edits reset
            assert len(state.next_date_overrides) == 0
            assert len(state.reviewed_sequences) == 0



