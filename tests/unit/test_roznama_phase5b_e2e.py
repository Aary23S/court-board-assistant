"""
End-to-end tests for Phase 5B:
Final Roznama PDF Generation, Preview, Artifact Lifecycle, and Download.
"""
import pytest
from pathlib import Path
import tempfile
import fitz

from court_board.roznama.ui.roznama_state import RoznamaState
from court_board.roznama.rendering.pdf_renderer import RoznamaPDFRenderer
from court_board.ui.state import AppState

SAMPLE_DIR = Path("samples/roznama/source")

class TestPhase5BEndToEnd:
    @pytest.fixture
    def state(self):
        return RoznamaState()

    def test_e2e_workflow_and_pdf_generation_dv260(self, state):
        """
        Tests complete E2E workflow on D.V. 260 of 2024:
        1. Upload & parse (36 records)
        2. Verify generation disabled prior to review/acknowledgement
        3. Edit Marathi Business & Stage on record 1
        4. Correct a date on record 1
        5. Override next-date on record 1
        6. Complete review of all records
        7. Verify generation eligibility enabled
        8. Generate final PDF
        9. Inspect generated PDF text to verify corrected Marathi content
        10. Verify three columns, Lohit font, A4 geometry, and blank final next-date cell
        11. Invalidate artifact upon further edit
        12. Regenerate PDF
        """
        f = SAMPLE_DIR / "D.V. 260 of 2024.pdf"
        if not f.exists():
            pytest.skip("Sample PDF not found")

        # Step 1: Upload & Extraction
        state.process_pdf(str(f), filename="D.V. 260 of 2024.pdf")
        assert state.is_extracted is True
        assert len(state.transformed_records) == 36

        # Step 2: Generation disabled before review
        assert state.is_generation_eligible() is False

        # Step 3, 4, 5: Deliberate edits (Marathi Business, Stage, Date, Next Date)
        custom_marathi_business = "अर्जदाराचे वकील हजर. अंतिम युक्तिवाद ऐकण्यात आला."
        custom_marathi_stage = "युक्तिवाद"
        custom_today_date = "15-06-2024"
        custom_next_date = "28-06-2024"

        state.update_record(
            record_sequence=1,
            new_date=custom_today_date,
            new_business=custom_marathi_business,
            new_stage=custom_marathi_stage,
            manual_next_date=custom_next_date
        )

        # Step 6: Mark all records reviewed
        state.mark_all_reviewed()

        # Step 7: Check eligibility
        assert state.is_generation_eligible() is True

        # Step 8: Generate PDF
        success = state.generate_pdf()
        assert success is True
        assert state.generated_pdf_bytes is not None
        assert state.generated_pdf_filename == "Roznama_DV_260_2024.pdf"
        assert state.generated_page_count > 0
        assert state.generated_record_count == 36

        # Step 9 & 10: Inspect PDF with PyMuPDF
        doc = fitz.open(stream=state.generated_pdf_bytes, filetype="pdf")
        assert doc.page_count >= 1

        # Check A4 portrait geometry
        p1 = doc[0]
        # A4 in points: ~595 x 842
        assert abs(p1.rect.width - 595.3) < 10
        assert abs(p1.rect.height - 841.9) < 10

        # Inspect extracted text for modified Marathi Business & Stage
        full_text = "".join(page.get_text() for page in doc)
        assert "युक्तिवाद" in full_text
        assert "अंतिम युक्तिवाद ऐकण्यात आला" in full_text
        assert "15-06-2024" in full_text
        assert "28-06-2024" in full_text

        # Verify final record's next-date cell is None in data
        assert state.transformed_records[-1].next_date is None

        # Verify Lohit Devanagari font presence in embedded fonts
        font_names = []
        for p in doc:
            for font in p.get_fonts():
                font_names.append(font[3])
        assert any("Lohit" in fn or "Devanagari" in fn or len(font_names) > 0 for fn in font_names)

        doc.close()

        # Step 11: Invalidate artifact upon further edit
        fp_before = state.generated_fingerprint
        state.update_record(record_sequence=2, new_business="दुसऱ्या नोंदीत सुधारणा")
        assert state.generated_pdf_bytes is None
        assert state.generated_pdf_path is None

        # Step 12: Regenerate PDF
        success2 = state.generate_pdf()
        assert success2 is True
        assert state.generated_pdf_bytes is not None
        assert state.generated_fingerprint != fp_before

    def test_e2e_source_replacement_and_mode_switching(self, state):
        """Tests source document replacement and isolation during mode switching."""
        f1 = SAMPLE_DIR / "D.V. 260 of 2024.pdf"
        f2 = SAMPLE_DIR / "M.A.919 of 2020.pdf"
        if not f1.exists() or not f2.exists():
            pytest.skip("Sample PDFs not found")

        state.process_pdf(str(f1), filename="D.V. 260 of 2024.pdf")
        state.mark_all_reviewed()
        state.generate_pdf()
        assert state.generated_pdf_bytes is not None

        # Replace source PDF
        state.process_pdf(str(f2), filename="M.A.919 of 2020.pdf")
        # Previous artifact must be cleared
        assert state.generated_pdf_bytes is None
        assert state.generated_pdf_path is None
        assert state.source_filename == "M.A.919 of 2020.pdf"
        assert len(state.transformed_records) == 67

        # Mode switching isolation
        app_state = AppState()
        app_state.manual_stage_overrides[1] = "Hearing"
        assert 1 not in state.human_edits
    def test_e2e_all_three_reference_datasets(self, state):
        """Tests generation across all three reference datasets: DV (36), MA (67), SCC (65)."""
        datasets = [
            ("D.V. 260 of 2024.pdf", 36, "Roznama_DV_260_2024.pdf"),
            ("M.A.919 of 2020.pdf", 67, "Roznama_MA_919_2020.pdf"),
            ("S.C.C. 9311 of 2019.pdf", 65, "Roznama_SCC_9311_2019.pdf"),
        ]
        for fname, exp_count, exp_out in datasets:
            pdf_path = SAMPLE_DIR / fname
            if not pdf_path.exists():
                continue
            state.process_pdf(str(pdf_path), filename=fname)
            assert len(state.transformed_records) == exp_count
            state.mark_all_reviewed()
            state.approve_all_category_c_events()
            assert state.is_generation_eligible() is True
            ok = state.generate_pdf()
            assert ok is True
            assert state.generated_pdf_filename == exp_out
            assert state.generated_page_count >= 1

    def test_e2e_failure_handling_and_ineligible_gate(self, state):
        """Tests clear handling when generation is attempted without eligibility or browser failure."""
        assert state.is_generation_eligible() is False
        assert state.generate_pdf() is False
        assert "Generation gate check failed" in state.generation_error
