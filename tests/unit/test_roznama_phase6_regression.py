"""
Unit and regression tests for Phase 6:
Devanagari Unicode Normalization & Standardized Template Fidelity.
"""
import pytest
from pathlib import Path
import fitz

from court_board.roznama.extraction.pua_normalizer import MarathiPUANormalizer
from court_board.roznama.parsing.record_parser import RecordBoundaryParser
from court_board.roznama.transformation.transformer import RoznamaTransformer
from court_board.roznama.rendering.pdf_renderer import RoznamaPDFRenderer
from court_board.roznama.domain.models import RoznamaHeader

SAMPLE_DIR = Path("samples/roznama/source")

class TestPhase6UnicodeNormalization:
    @pytest.fixture
    def normalizer(self):
        return MarathiPUANormalizer()

    def test_pre_base_velanti_reordering(self, normalizer):
        """Verifies pre-base velanti (U+093F) moves after intended consonant or conjunct."""
        # Simple consonants
        assert normalizer.normalize("िदनांक")[0] == "दिनांक"
        assert normalizer.normalize("िवड")[0] == "विड"
        assert normalizer.normalize("िधकारी")[0] == "धिकारी"
        assert normalizer.normalize("िकरकोळ")[0] == "किरकोळ"
        assert normalizer.normalize("ित")[0] == "ति"
        assert normalizer.normalize("िशक")[0] == "शिक"

    def test_pre_base_velanti_with_conjuncts(self, normalizer):
        """Verifies velanti attaches properly to multi-consonant conjuncts."""
        # \u093f + स + ् + थ + त + ि -> स्थिति
        raw_sthiti = "\u093f\u0938\u094d\u0925\u0924\u093f"
        assert normalizer.normalize(raw_sthiti)[0] == "स्थिति"

    def test_velanti_combined_with_reph(self, normalizer):
        """Verifies pre-base velanti works seamlessly with reph markers."""
        # िफया\ue77aदी -> फिर्यादी
        raw_phiryadi = "िफया\ue77aदी"
        norm, _ = normalizer.normalize(raw_phiryadi)
        assert norm == "फिर्यादी"

        # Court / Korta
        raw_korta = "मे. कोटा\ue77aसमोरर िफया\ue77aदी"
        norm_korta, _ = normalizer.normalize(raw_korta)
        assert "कोर्टासमोरर" in norm_korta
        assert "फिर्यादी" in norm_korta

    def test_split_vowel_composition(self, normalizer):
        """Verifies decomposed aa + e (U+093E + U+0947) is composed into o-matra (U+094B)."""
        raw_covid = "काेिवड संसग\ue77a"
        norm, _ = normalizer.normalize(raw_covid)
        assert norm == "कोविड संसर्ग"

        raw_aropi = "आराेपी"
        assert normalizer.normalize(raw_aropi)[0] == "आरोपी"

    def test_already_correct_unicode_unchanged(self, normalizer):
        """Verifies already-correct Unicode Devanagari text remains completely unchanged."""
        already_correct = "मुख्य न्यायदंडाधिकारी, नाशिक श्री. जे. व्ही. पालीवाल फिर्यादी अर्जदार आदेश अहवाल"
        norm, unmapped = normalizer.normalize(already_correct)
        assert norm == already_correct
        assert unmapped == []

    def test_normalization_idempotency(self, normalizer):
        """Verifies that calling normalize() twice does not introduce additional changes."""
        raw = "मे. कोटा\ue77aसमोरर िफया\ue77aदी गैरहजर काेिवड संसग\ue77a अज\ue77aदार"
        step1, _ = normalizer.normalize(raw)
        step2, _ = normalizer.normalize(step1)
        assert step1 == step2

    def test_preserve_english_and_punctuation(self, normalizer):
        """Verifies English characters, numerals, and punctuation are preserved."""
        mixed = "Party Name: Business: Exh.1 dated 01.11.2025 returned! (Adjournment)"
        norm, _ = normalizer.normalize(mixed)
        assert norm == mixed

    def test_double_judge_vowel_cleanup(self, normalizer):
        """Verifies cleanup of double vowel typo from legacy title text."""
        raw_judge = "यांचे \ue219यायालयात : \ue2a4ी .जे .\ue222ही.पालीवाल"
        norm, _ = normalizer.normalize(raw_judge)
        assert norm == "यांचे न्यायालयात : श्री .जे .व्ही.पालीवाल"
        assert "श्रीी" not in norm


class TestPhase6DocumentRegression:
    def test_all_three_reference_record_counts_and_order(self):
        """Verifies 36 (DV), 67 (MA), 65 (SCC) counts and sequence preservation."""
        expected = [
            ("D.V. 260 of 2024.pdf", 36),
            ("M.A.919 of 2020.pdf", 67),
            ("S.C.C. 9311 of 2019.pdf", 65),
        ]
        parser = RecordBoundaryParser()
        transformer = RoznamaTransformer()

        total = 0
        for fname, count in expected:
            f = SAMPLE_DIR / fname
            if not f.exists():
                continue
            recs = parser.parse_document(str(f))
            assert len(recs) == count
            trans = transformer.transform(recs)
            assert len(trans) == count
            # Sequence order continuous 1..N
            assert [r.record_sequence for r in trans] == list(range(1, count + 1))
            total += count

        assert total == 168

    @pytest.fixture
    def normalizer(self):
        return MarathiPUANormalizer()

    def test_record_14_pratiniyukti_normalization(self, normalizer):
        """Verifies Record 14 \ue955ित िनयु\ue8c0त्◌ीवर is correctly normalized to प्रतिनियुक्तीवर."""
        raw14 = "Business: मे. कोट\ue77a \ue955ित िनयु\ue8c0त्◌ीवर अज\ue77aदार हजर वकील हजर"
        norm14, _ = normalizer.normalize(raw14)
        assert "प्रतिनियुक्तीवर" in norm14
        assert "प्रति नियुक्तीवर" not in norm14
        assert "प्रित" not in norm14
        assert "त्◌ी" not in norm14
        assert "कोर्ट" in norm14

    def test_prati_spacing_preservation(self, normalizer):
        """Verifies genuine standalone 'प्रति' spaces are not collapsed."""
        # e.g. प्रति महिना, प्रति वर्षी, प्रति प्रतिवादी
        text = "अर्जदाराने प्रति महिना रुपये ५००० द्यावे. प्रति वर्षी अहवाल सादर करावा."
        norm, _ = normalizer.normalize(text)
        assert "प्रति महिना" in norm
        assert "प्रति वर्षी" in norm

    def test_next_date_derivation_counts_and_continuity(self):
        """
        Verifies exact next-date derivation across all 3 source documents:
        - D.V. 260 of 2024: 35 non-empty, exactly 1 blank (total 36)
        - M.A. 919 of 2020: 66 non-empty, exactly 1 blank (total 67)
        - S.C.C. 9311 of 2019: 64 non-empty, exactly 1 blank (total 65)
        - Contiguity: rec[i].next_date == rec[i+1].hearing_date for all 0 <= i < N-1
        """
        datasets = [
            ("D.V. 260 of 2024.pdf", 36, 35, 1),
            ("M.A.919 of 2020.pdf", 67, 66, 1),
            ("S.C.C. 9311 of 2019.pdf", 65, 64, 1),
        ]
        parser = RecordBoundaryParser()
        transformer = RoznamaTransformer()

        for fname, total_exp, non_empty_exp, blank_exp in datasets:
            f = SAMPLE_DIR / fname
            if not f.exists():
                continue
            src_records = parser.parse_document(str(f))
            assert len(src_records) == total_exp
            trans_records = transformer.transform(src_records)
            assert len(trans_records) == total_exp

            non_empty_count = sum(1 for r in trans_records if r.next_date is not None and str(r.next_date).strip() != "")
            blank_count = sum(1 for r in trans_records if r.next_date is None or str(r.next_date).strip() == "")

            assert non_empty_count == non_empty_exp
            assert blank_count == blank_exp
            assert trans_records[-1].next_date is None

            # Verify contiguity for all adjacent records
            for i in range(len(trans_records) - 1):
                assert trans_records[i].next_date == src_records[i + 1].hearing_date

    def test_all_eight_investigated_records_fidelity(self):
        """Verifies records 1, 2, 6, 14, 20, 42, 43, 52 against expected normalized Marathi text."""
        f = SAMPLE_DIR / "M.A.919 of 2020.pdf"
        if not f.exists():
            pytest.skip("Sample PDF not found")

        parser = RecordBoundaryParser()
        transformer = RoznamaTransformer()
        records = transformer.transform(parser.parse_document(str(f)))
        r_map = {r.record_sequence: r for r in records}

        # 1. Record 1: Lockdown
        assert "लॉकडाउन. Stage: आदेश" == r_map[1].proceedings_detail

        # 2. Record 2: Courtasamor & Phiryadi
        assert "कोर्टासमोर" in r_map[2].proceedings_detail
        assert "फिर्यादी" in r_map[2].proceedings_detail
        assert "िफ" not in r_map[2].proceedings_detail

        # 3. Record 6: Arjadarache Yuktivad
        assert "कोर्टासमोर" in r_map[6].proceedings_detail
        assert "अर्जदाराचे" in r_map[6].proceedings_detail
        assert "युक्तीवाद" in r_map[6].proceedings_detail

        # 4. Record 14: Court Pratiniyukti
        assert "कोर्ट" in r_map[14].proceedings_detail
        assert "प्रति" in r_map[14].proceedings_detail
        assert "नियुक्तीवर" in r_map[14].proceedings_detail
        assert "प्रित" not in r_map[14].proceedings_detail
        assert "◌" not in r_map[14].proceedings_detail

        # 5. Record 20: Arjadar gairhajar
        assert "अर्जदार गैरहजर" in r_map[20].proceedings_detail

        # 6. Record 42: Courtasamor Arjadar hajar
        assert "कोर्टासमोर" in r_map[42].proceedings_detail
        assert "अर्जदार हजर" in r_map[42].proceedings_detail

        # 7. Record 43: Courtasamor Arjadar hajar va vakil gairhajar
        assert "कोर्टासमोर" in r_map[43].proceedings_detail
        assert "अर्जदार हजर व वकील गैरहजर" in r_map[43].proceedings_detail

        # 8. Record 52: Nyayalayasamaksha Phiryadi hajar
        assert "न्यायालयासमक्ष" in r_map[52].proceedings_detail
        assert "फिर्यादी" in r_map[52].proceedings_detail
        assert "िफ" not in r_map[52].proceedings_detail

    def test_pdf_rendering_regression_and_font_embedding(self, tmp_path):
        """Renders M.A. 919 and checks font embedding and lack of corrupted marks."""
        f = SAMPLE_DIR / "M.A.919 of 2020.pdf"
        if not f.exists():
            pytest.skip("Sample PDF not found")

        parser = RecordBoundaryParser()
        transformer = RoznamaTransformer()
        records = transformer.transform(parser.parse_document(str(f)))

        renderer = RoznamaPDFRenderer()
        out_pdf = tmp_path / "test_ma919_normalized.pdf"
        renderer.render(records, out_pdf, header=RoznamaHeader(case_number="M.A. 919 of 2020"))

        assert out_pdf.exists()
        doc = fitz.open(str(out_pdf))
        assert doc.page_count >= 1

        # Check font embedding
        fonts = []
        for p in doc:
            for font in p.get_fonts():
                fonts.append(font[3])
        assert any("Lohit" in fn or len(fonts) > 0 for fn in fonts)

        full_text = "".join(p.get_text() for p in doc)
        assert "फिर्यादी" in full_text
        assert "कोर्टासमोर" in full_text
        assert "अर्जदार" in full_text
        assert "कोविड" in full_text

        # Verify no "---" placeholder in header if not specified
        assert "सीएनआर क्रमांक: ---" not in full_text

        # Verify final record has blank next-date
        assert records[-1].next_date is None
