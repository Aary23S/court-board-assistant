"""
Unit and regression tests for Phase 3B: Roznama Transformation Engine.
Verifies Rules A, B, C, D, edge cases, and mandatory invariants.
"""
import pytest
from pathlib import Path

from court_board.roznama.domain.models import SourceProceedingRecord, RoznamaRecord
from court_board.roznama.transformation.transformer import RoznamaTransformer
from court_board.roznama.parsing.record_parser import RecordBoundaryParser

SAMPLE_DIR = Path("samples/roznama/source")

class TestRoznamaTransformerUnit:
    @pytest.fixture
    def transformer(self):
        return RoznamaTransformer()

    def test_rule_a_business_and_stage_combination(self, transformer):
        # 1. Standard combination
        recs = [
            SourceProceedingRecord(
                record_sequence=1, hearing_date="10-01-2026",
                business="अर्जदार गैरहजर", stage="प्रथम आदेश",
                source_page_start=1, source_page_end=1
            )
        ]
        out = transformer.transform(recs)
        assert out[0].proceedings_detail == "अर्जदार गैरहजर. Stage: प्रथम आदेश"

    def test_rule_a_punctuation_avoid_double_dot(self, transformer):
        # 2. Business already ends with period
        recs = [
            SourceProceedingRecord(
                record_sequence=1, hearing_date="10-01-2026",
                business="लॉकडाउन.", stage="आदेश",
                source_page_start=1, source_page_end=1
            )
        ]
        out = transformer.transform(recs)
        assert out[0].proceedings_detail == "लॉकडाउन. Stage: आदेश"

    def test_rule_a_placeholder_stage(self, transformer):
        # 3. Stage has placeholder '----'
        recs = [
            SourceProceedingRecord(
                record_sequence=1, hearing_date="10-01-2026",
                business="न्यायालय रजेवर", stage="----",
                source_page_start=1, source_page_end=1
            )
        ]
        out = transformer.transform(recs)
        assert out[0].proceedings_detail == "न्यायालय रजेवर. Stage: ----"

    def test_rule_b_and_c_date_mappings(self, transformer):
        recs = [
            SourceProceedingRecord(
                record_sequence=1, hearing_date="01-05-2026",
                business="कामकाज १", stage="आदेश",
                source_page_start=1, source_page_end=1
            ),
            SourceProceedingRecord(
                record_sequence=2, hearing_date="15-05-2026",
                business="कामकाज २", stage="सुनावणी",
                source_page_start=1, source_page_end=1
            ),
            SourceProceedingRecord(
                record_sequence=3, hearing_date="30-05-2026",
                business="कामकाज ३", stage="निकाल",
                source_page_start=1, source_page_end=1
            ),
        ]
        out = transformer.transform(recs)

        # Invariant checks
        assert len(out) == 3
        # Rec 0: today=01-05, next=15-05
        assert out[0].today_date == "01-05-2026"
        assert out[0].next_date == "15-05-2026"

        # Rec 1: today=15-05, next=30-05
        assert out[1].today_date == "15-05-2026"
        assert out[1].next_date == "30-05-2026"

        # Rec 2 (Final): today=30-05, next=None
        assert out[2].today_date == "30-05-2026"
        assert out[2].next_date is None

    def test_rule_d_duplicate_dates_and_repeated_sn(self, transformer):
        recs = [
            SourceProceedingRecord(
                record_sequence=1, serial_number="1", hearing_date="14-02-2025",
                business="पहिले कामकाज", stage="अहवाल",
                source_page_start=1, source_page_end=1
            ),
            SourceProceedingRecord(
                record_sequence=2, serial_number="1", hearing_date="14-02-2025",
                business="दुसरे कामकाज", stage="अहवाल",
                source_page_start=1, source_page_end=1
            ),
        ]
        out = transformer.transform(recs)
        assert len(out) == 2
        assert out[0].record_sequence == 1
        assert out[1].record_sequence == 2
        assert out[0].today_date == "14-02-2025"
        assert out[0].next_date == "14-02-2025"
        assert out[1].next_date is None

    def test_empty_input(self, transformer):
        assert transformer.transform([]) == []

    def test_invalid_duplicate_sequence_raises(self, transformer):
        recs = [
            SourceProceedingRecord(
                record_sequence=1, hearing_date="01-05-2026",
                business="A", stage="B", source_page_start=1, source_page_end=1
            ),
            SourceProceedingRecord(
                record_sequence=1, hearing_date="02-05-2026",
                business="C", stage="D", source_page_start=1, source_page_end=1
            )
        ]
        with pytest.raises(ValueError, match="Duplicate record_sequence"):
            transformer.transform(recs)


class TestRoznamaTransformerRegression:
    @pytest.fixture
    def setup(self):
        return RecordBoundaryParser(), RoznamaTransformer()

    def _verify_mandatory_invariants(self, source_recs, roznama_recs):
        # Mandatory Invariant 1: Equal count
        assert len(source_recs) == len(roznama_recs)

        # Mandatory Invariant 2: Lookahead next date
        for idx in range(len(roznama_recs) - 1):
            assert (
                roznama_recs[idx].next_date == roznama_recs[idx + 1].today_date
            ), f"Next-date mismatch at index {idx}: {roznama_recs[idx].next_date} != {roznama_recs[idx+1].today_date}"

        # Mandatory Invariant 3: Final record next_date is None
        assert roznama_recs[-1].next_date is None

        # Mandatory Invariant 4: Exact sequence match
        for idx in range(len(roznama_recs)):
            assert roznama_recs[idx].record_sequence == source_recs[idx].record_sequence

    def test_dv_sample_transformation(self, setup):
        parser, transformer = setup
        f = SAMPLE_DIR / "D.V. 260 of 2024.pdf"
        if not f.exists():
            pytest.skip("Sample PDF not found")

        source_recs = parser.parse_document(str(f))
        assert len(source_recs) == 36

        roznama_recs = transformer.transform(source_recs)
        self._verify_mandatory_invariants(source_recs, roznama_recs)

        # Check First record
        assert roznama_recs[0].today_date == "30-05-2024"
        assert roznama_recs[0].next_date == "20-06-2024"
        assert "Stage: प्रथम आदेश" in roznama_recs[0].proceedings_detail

        # Check Middle record (idx 17, SN 18)
        assert roznama_recs[17].record_sequence == 18
        assert roznama_recs[17].today_date == "16-06-2025"
        assert roznama_recs[17].next_date == "14-07-2025"

        # Check Final record
        assert roznama_recs[-1].today_date == "22-10-2026"
        assert roznama_recs[-1].next_date is None
        assert "Stage: काढुन घेतला" in roznama_recs[-1].proceedings_detail

    def test_ma_sample_transformation(self, setup):
        parser, transformer = setup
        f = SAMPLE_DIR / "M.A.919 of 2020.pdf"
        if not f.exists():
            pytest.skip("Sample PDF not found")

        source_recs = parser.parse_document(str(f))
        assert len(source_recs) == 67

        roznama_recs = transformer.transform(source_recs)
        self._verify_mandatory_invariants(source_recs, roznama_recs)

        # Check serial number reset boundary (Page 2 Rec 14 -> Page 3 Rec 15)
        # Rec 14: 14-03-2022
        # Rec 15: 07-04-2022
        assert roznama_recs[13].record_sequence == 14
        assert roznama_recs[13].today_date == "14-03-2022"
        assert roznama_recs[13].next_date == "07-04-2022"

        assert roznama_recs[14].record_sequence == 15
        assert roznama_recs[14].today_date == "07-04-2022"
        assert roznama_recs[14].next_date == "28-04-2022"

        # Final record
        assert roznama_recs[-1].today_date == "21-10-2026"
        assert roznama_recs[-1].next_date is None

    def test_scc_sample_transformation(self, setup):
        parser, transformer = setup
        f = SAMPLE_DIR / "S.C.C. 9311 of 2019.pdf"
        if not f.exists():
            pytest.skip("Sample PDF not found")

        source_recs = parser.parse_document(str(f))
        assert len(source_recs) == 65

        roznama_recs = transformer.transform(source_recs)
        self._verify_mandatory_invariants(source_recs, roznama_recs)

        # First record
        assert roznama_recs[0].today_date == "02-01-2020"
        assert roznama_recs[0].next_date == "11-02-2020"
        assert "Stage: ----" in roznama_recs[0].proceedings_detail

        # Final record
        assert roznama_recs[-1].today_date == "23-10-2026"
        assert roznama_recs[-1].next_date is None
        assert "Stage: न्यायिनर्णय" in roznama_recs[-1].proceedings_detail