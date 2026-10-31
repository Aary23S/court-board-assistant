"""
Unit and regression tests for Phase 4: Roznama PDF Renderer with Lohit Marathi.
"""
import pytest
from pathlib import Path
import fitz

from court_board.roznama.domain.models import RoznamaRecord, RoznamaHeader
from court_board.roznama.rendering.font_manager import FontManager
from court_board.roznama.rendering.html_builder import RoznamaHTMLBuilder
from court_board.roznama.rendering.pdf_renderer import RoznamaPDFRenderer
from court_board.roznama.parsing.record_parser import RecordBoundaryParser
from court_board.roznama.transformation.transformer import RoznamaTransformer

SAMPLE_DIR = Path("samples/roznama/source")

class TestFontManager:
    def test_font_asset_exists(self):
        fm = FontManager()
        assert fm.validate_font_asset() is True
        assert fm.font_path.exists()
        assert fm.font_path.stat().st_size > 50000

    def test_base64_encoding_non_empty(self):
        fm = FontManager()
        b64 = fm.get_base64_font()
        assert len(b64) > 10000

class TestRoznamaHTMLBuilder:
    def test_html_contains_three_columns(self):
        builder = RoznamaHTMLBuilder()
        recs = [
            RoznamaRecord(
                record_sequence=1, today_date="01-05-2026",
                proceedings_detail="अर्जदार हजर. Stage: प्रथम आदेश",
                next_date="15-05-2026", judge_designation="न्यायाधीश"
            )
        ]
        html = builder.build_html(recs)
        assert "आजची दिनांक" in html
        assert "दैनंदिन कामकाज तपशील" in html
        assert "पुढे/निकाल तारीख" in html
        assert "01-05-2026" in html
        assert "15-05-2026" in html
        assert "Lohit Devanagari" in html

class TestRoznamaPDFRenderer:
    @pytest.fixture
    def renderer(self):
        return RoznamaPDFRenderer()

    def test_pdf_generation_and_dimensions(self, renderer, tmp_path):
        recs = [
            RoznamaRecord(
                record_sequence=1, today_date="30-05-2024",
                proceedings_detail="मे िपठािसन अिधकारी उन्हाळी सुटीवर पक्षकार गैरहजर प्रकरण तहकुब. Stage: प्रथम आदेश",
                next_date="20-06-2024", judge_designation="न्यायाधीश"
            ),
            RoznamaRecord(
                record_sequence=2, today_date="20-06-2024",
                proceedings_detail="न्यायालयासमक्ष पुकारले असता पक्षकार गैरहजर. Stage: युक्तीवाद",
                next_date=None, judge_designation="न्यायाधीश"
            )
        ]
        out_pdf = tmp_path / "test_out.pdf"
        renderer.render(recs, out_pdf)

        assert out_pdf.exists()
        assert out_pdf.stat().st_size > 1000

        # Inspect generated PDF
        doc = fitz.open(str(out_pdf))
        assert len(doc) >= 1
        page = doc[0]
        # Verify A4 Portrait dimensions (~595 x 842 pt)
        w, h = page.rect.width, page.rect.height
        assert 594.0 <= w <= 596.0
        assert 841.0 <= h <= 843.0

        # Verify embedded Lohit font
        font_names = [f[3] for f in page.get_fonts()]
        assert any("Lohit-Devanagari" in name for name in font_names)

        doc.close()

    def test_full_dv_sample_pdf_generation(self, renderer, tmp_path):
        f = SAMPLE_DIR / "D.V. 260 of 2024.pdf"
        if not f.exists():
            pytest.skip("Sample PDF not found")

        parser = RecordBoundaryParser()
        transformer = RoznamaTransformer()

        source_recs = parser.parse_document(str(f))
        roznama_recs = transformer.transform(source_recs)

        out_pdf = tmp_path / "dv_260_generated.pdf"
        header = RoznamaHeader(case_number="म.सं.कौ.हिं.का.अर्ज/260/2024")
        renderer.render(roznama_recs, out_pdf, header=header)

        assert out_pdf.exists()
        doc = fitz.open(str(out_pdf))
        # 36 records comfortably paginated across continuous flow pages
        assert len(doc) >= 5
        doc.close()

