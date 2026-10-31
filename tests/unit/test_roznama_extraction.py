"""
Unit and regression tests for Phase 2: PDF Extraction Engine & Marathi OCR.
"""
import pytest
from pathlib import Path

from court_board.roznama.extraction.pua_normalizer import (
    MarathiPUANormalizer,
    MARATHI_PUA_GLYPH_MAP
)
from court_board.roznama.extraction.native_extractor import NativePDFExtractor
from court_board.roznama.extraction.analyzer import PDFPageAnalyzer
from court_board.roznama.extraction.ocr_engine import MarathiOCREngine

SAMPLE_DIR = Path("samples/roznama/source")

class TestMarathiPUANormalizer:
    def test_pua_mapping_count(self):
        # 39 verified PUA glyphs from e-Courts PDFs
        assert len(MARATHI_PUA_GLYPH_MAP) == 39

    def test_normalize_known_pua(self):
        normalizer = MarathiPUANormalizer()
        
        # Test individual key glyphs
        res, unmapped = normalizer.normalize("मु\ue20eय")
        assert res == "मुख्य"
        assert unmapped == []

        res, unmapped = normalizer.normalize("\ue2a2करण")
        assert res == "प्रकरण"
        assert unmapped == []

        res, unmapped = normalizer.normalize("\ue29fमांक")
        assert res == "क्रमांक"
        assert unmapped == []

        res, unmapped = normalizer.normalize("अज\ue77a")
        assert res == "अर्ज"
        assert unmapped == []

        res, unmapped = normalizer.normalize("प\ue8bdकार")
        assert res == "पक्षकार"
        assert unmapped == []

        res, unmapped = normalizer.normalize("यु\ue8c0तीवाद")
        assert res == "युक्तीवाद"
        assert unmapped == []

    def test_unmapped_pua_tracking(self):
        normalizer = MarathiPUANormalizer()
        # \uE999 is not in the map
        res, unmapped = normalizer.normalize("Test \ue999 text")
        assert unmapped == ["\ue999"]
        assert "\ue999" in res  # Never silently discarded

class TestNativePDFExtractor:
    def test_page_counts(self):
        f1 = SAMPLE_DIR / "D.V. 260 of 2024.pdf"
        f2 = SAMPLE_DIR / "M.A.919 of 2020.pdf"
        f3 = SAMPLE_DIR / "S.C.C. 9311 of 2019.pdf"

        if not f1.exists():
            pytest.skip("Sample PDFs not available in tests directory")

        with NativePDFExtractor(str(f1)) as ext:
            assert ext.page_count == 9

        with NativePDFExtractor(str(f2)) as ext:
            assert ext.page_count == 11

        with NativePDFExtractor(str(f3)) as ext:
            assert ext.page_count == 12

    def test_page_dimensions(self):
        f1 = SAMPLE_DIR / "D.V. 260 of 2024.pdf"
        if not f1.exists():
            pytest.skip("Sample PDFs not available")

        with NativePDFExtractor(str(f1)) as ext:
            w, h = ext.get_page_dimensions(1)
            assert 595.0 <= w <= 596.0
            assert 841.0 <= h <= 842.0

class TestPDFPageAnalyzer:
    def test_dv_sample_analysis(self):
        f1 = SAMPLE_DIR / "D.V. 260 of 2024.pdf"
        if not f1.exists():
            pytest.skip("Sample PDFs not available")

        analyzer = PDFPageAnalyzer()
        summary = analyzer.analyze_document(str(f1))

        assert summary.total_pages == 9
        assert summary.overall_method == "NATIVE_TEXT"
        assert summary.overall_quality == "EXCELLENT"
        assert summary.total_unmapped_pua == 0
        assert summary.total_pua_detected > 0

    def test_ma_sample_analysis(self):
        f2 = SAMPLE_DIR / "M.A.919 of 2020.pdf"
        if not f2.exists():
            pytest.skip("Sample PDFs not available")

        analyzer = PDFPageAnalyzer()
        summary = analyzer.analyze_document(str(f2))

        assert summary.total_pages == 11
        assert summary.overall_method == "NATIVE_TEXT"
        assert summary.overall_quality == "EXCELLENT"
        assert summary.total_unmapped_pua == 0

    def test_scc_sample_analysis(self):
        f3 = SAMPLE_DIR / "S.C.C. 9311 of 2019.pdf"
        if not f3.exists():
            pytest.skip("Sample PDFs not available")

        analyzer = PDFPageAnalyzer()
        summary = analyzer.analyze_document(str(f3))

        assert summary.total_pages == 12
        assert summary.overall_method == "NATIVE_TEXT"
        assert summary.overall_quality == "EXCELLENT"
        assert summary.total_unmapped_pua == 0

class TestMarathiOCREngine:
    def test_ocr_availability_reporting(self):
        engine = MarathiOCREngine()
        # Even if tesseract is not in system PATH on this environment, it must gracefully report status
        assert isinstance(engine.is_available, bool)
        
        # Test fallback behavior when unavailable
        if not engine.is_available:
            res = engine.ocr_page("dummy.pdf", 1)
            assert res["success"] is False
            assert "Tesseract" in res["error"]

