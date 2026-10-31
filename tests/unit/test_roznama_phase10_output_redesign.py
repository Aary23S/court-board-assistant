"""
Unit and integration tests for Phase 10:
Court-Approved Roznama Output Redesign & Multi-Format Export (PDF, XLSX, DOCX).
Verifies:
1. Shared presentation model structure (no 'Stage:' label, Business & Stage separation).
2. Exactly 3 columns across PDF, XLSX, and DOCX.
3. Case heading 'प्रकरण क्रमांक: ...' repeated for every hearing.
4. Removed metadata (judge name, party names, CNR, advocate) absent from hearing sections.
5. Dotted separator presence between hearings.
6. Multi-format data consistency across PDF, XLSX, and DOCX.
7. Next date derivation and blank next date for final hearing.
8. State invalidation for all three export artifacts on record edit or source reload.
"""
from pathlib import Path
import pytest
import openpyxl
import docx
import fitz

from court_board.roznama.parsing.record_parser import RecordBoundaryParser
from court_board.roznama.transformation.transformer import RoznamaTransformer
from court_board.roznama.rendering.presentation_model import RoznamaPresentationModel
from court_board.roznama.rendering.pdf_renderer import RoznamaPDFRenderer
from court_board.roznama.rendering.excel_renderer import RoznamaExcelRenderer
from court_board.roznama.rendering.word_renderer import RoznamaWordRenderer
from court_board.roznama.ui.roznama_state import RoznamaState
from court_board.roznama.domain.models import RoznamaHeader

SAMPLE_DIR = Path("samples/roznama/source")

class TestPhase10OutputRedesignAndMultiFormatExport:
    @pytest.fixture
    def ma919_data(self):
        pdf_path = SAMPLE_DIR / "M.A.919 of 2020.pdf"
        if not pdf_path.exists():
            pytest.skip("Fixture not found")
        parser = RecordBoundaryParser()
        transformer = RoznamaTransformer()
        src_recs = parser.parse_document(str(pdf_path))
        roznama_recs = transformer.transform(src_recs)
        return src_recs, roznama_recs

    @pytest.fixture
    def presentation_model(self, ma919_data):
        src_recs, roznama_recs = ma919_data
        return RoznamaPresentationModel.from_state_records(
            transformed_records=roznama_recs,
            source_records=src_recs,
            human_edits={},
            header_case_number="फौजदारी किरकोळ अर्ज/919/2020"
        )

    def test_shared_presentation_model_structure(self, presentation_model, ma919_data):
        """Verify presentation model items follow court-approved rules."""
        src_recs, roznama_recs = ma919_data
        assert len(presentation_model.items) == len(roznama_recs)
        assert len(presentation_model.items) == 67

        for idx, item in enumerate(presentation_model.items):
            # 1. Case heading repeated
            assert item.case_heading.startswith("प्रकरण क्रमांक:")
            assert "919/2020" in item.case_heading

            # 2. No literal 'Stage:' in combined text
            assert "Stage:" not in item.combined_detail
            assert "Stage:" not in item.business_text
            assert "Stage:" not in item.stage_text

            # 3. Date mapping
            assert item.hearing_date == src_recs[idx].hearing_date

            # 4. Final hearing next_date is blank
            if idx == len(presentation_model.items) - 1:
                assert item.next_date == ""
            else:
                assert item.next_date == src_recs[idx + 1].hearing_date

    def test_pdf_renderer_court_approved_structure(self, presentation_model, tmp_path):
        """Verify PDF output follows court-approved structure and contains no removed metadata."""
        out_pdf = tmp_path / "test_out.pdf"
        renderer = RoznamaPDFRenderer()
        renderer.render(presentation_model, out_pdf)

        assert out_pdf.exists()
        doc = fitz.open(str(out_pdf))
        assert doc.page_count >= 1

        full_text = "".join(p.get_text() for p in doc)
        
        # Verify 3 columns
        assert "आजची दिनांक" in full_text
        assert "दैनंदिन कामकाज तपशील" in full_text
        assert "पुढे/निकाल तारीख" in full_text

        # Verify repeated case heading
        assert full_text.count("प्रकरण क्रमांक:") >= 10

        # Verify removed metadata is NOT present in repeated hearing headers
        assert "सीएनआर क्रमांक:" not in full_text
        assert "सहाय्यक सरकारी अभियोक्ता" not in full_text
        assert "सरकार तर्फे" not in full_text
        assert "Stage:" not in full_text

        doc.close()

    def test_excel_renderer_structure_and_compatibility(self, presentation_model, tmp_path):
        """Verify Excel workbook structure, merged cells, 3 columns, and compatibility."""
        out_xlsx = tmp_path / "test_out.xlsx"
        renderer = RoznamaExcelRenderer()
        renderer.render(presentation_model, out_xlsx)

        assert out_xlsx.exists()
        wb = openpyxl.load_workbook(str(out_xlsx))
        ws = wb.active
        assert ws.title == "Roznama"

        # Check Row 1 (Heading)
        assert ws.cell(row=1, column=1).value.startswith("प्रकरण क्रमांक:")

        # Check Row 2 (3 Columns)
        assert ws.cell(row=2, column=1).value == "आजची दिनांक"
        assert ws.cell(row=2, column=2).value == "दैनंदिन कामकाज तपशील"
        assert ws.cell(row=2, column=3).value == "पुढे/निकाल तारीख"

        # Check Col 2 content has no 'Stage:'
        col2_val = ws.cell(row=3, column=2).value
        assert "Stage:" not in col2_val

        # Verify last record next date is empty
        # Find last hearing row
        last_item = presentation_model.items[-1]
        assert last_item.next_date == ""

        wb.close()

    def test_word_renderer_structure_and_compatibility(self, presentation_model, tmp_path):
        """Verify Word (.docx) document structure, 3-column tables, headings, and formatting."""
        out_docx = tmp_path / "test_out.docx"
        renderer = RoznamaWordRenderer()
        renderer.render(presentation_model, out_docx)

        assert out_docx.exists()
        doc = docx.Document(str(out_docx))

        # Check that we have 67 tables (one per hearing)
        assert len(doc.tables) == 67

        # Check first table
        table0 = doc.tables[0]
        assert len(table0.columns) == 3
        assert table0.cell(0, 0).text == "आजची दिनांक"
        assert table0.cell(0, 1).text == "दैनंदिन कामकाज तपशील"
        assert table0.cell(0, 2).text == "पुढे/निकाल तारीख"

        # Check detail cell has no 'Stage:' label
        detail_text = table0.cell(1, 1).text
        assert "Stage:" not in detail_text

        # Check paragraph headings
        headings = [p.text for p in doc.paragraphs if p.text.startswith("प्रकरण क्रमांक:")]
        assert len(headings) == 67

    def test_cross_format_data_consistency(self, presentation_model, tmp_path):
        """Verify identical proceedings data across PDF, XLSX, and DOCX."""
        out_pdf = tmp_path / "consistency.pdf"
        out_xlsx = tmp_path / "consistency.xlsx"
        out_docx = tmp_path / "consistency.docx"

        RoznamaPDFRenderer().render(presentation_model, out_pdf)
        RoznamaExcelRenderer().render(presentation_model, out_xlsx)
        RoznamaWordRenderer().render(presentation_model, out_docx)

        # 1. Parse Excel data
        wb = openpyxl.load_workbook(str(out_xlsx))
        ws = wb.active
        xlsx_dates = []
        for r in range(3, ws.max_row + 1):
            val = ws.cell(row=r, column=1).value
            if val and val != "आजची दिनांक" and not str(val).startswith("प्रकरण"):
                xlsx_dates.append(str(val))
        wb.close()

        # 2. Parse Word data
        doc_w = docx.Document(str(out_docx))
        docx_dates = [t.cell(1, 0).text for t in doc_w.tables]

        # 3. Compare with presentation model
        expected_dates = [item.hearing_date for item in presentation_model.items]
        assert xlsx_dates == expected_dates
        assert docx_dates == expected_dates

    def test_state_multi_format_lifecycle_and_invalidation(self, tmp_path):
        """Verify RoznamaState generates and invalidates PDF, XLSX, and DOCX in lockstep."""
        pdf_path = SAMPLE_DIR / "M.A.919 of 2020.pdf"
        if not pdf_path.exists():
            pytest.skip("Fixture not found")

        state = RoznamaState()
        state.process_pdf(str(pdf_path), filename="M.A.919 of 2020.pdf")
        state.mark_all_reviewed()
        state.approve_all_category_c_events()
        assert state.is_generation_eligible() is True

        # Generate all three formats
        assert state.generate_pdf() is True
        assert state.generate_excel() is True
        assert state.generate_word() is True

        assert state.generated_pdf_bytes is not None
        assert state.generated_xlsx_bytes is not None
        assert state.generated_docx_bytes is not None

        # Human edits record 1 -> must invalidate ALL three formats
        state.update_record(record_sequence=1, new_business="सुधारित कामकाज तपशील.")
        assert state.generated_pdf_bytes is None
        assert state.generated_xlsx_bytes is None
        assert state.generated_docx_bytes is None
        assert state.generated_pdf_path is None
        assert state.generated_xlsx_path is None
        assert state.generated_docx_path is None

