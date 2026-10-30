"""
Unit and regression tests for Phase 3 Part A: Record Boundary Parsing.
"""
import pytest
from pathlib import Path

from court_board.roznama.parsing.record_parser import RecordBoundaryParser

SAMPLE_DIR = Path("samples/roznama/source")

class TestRecordBoundaryParser:
    @pytest.fixture
    def parser(self):
        return RecordBoundaryParser()

    def test_dv_sample_record_count(self, parser):
        f = SAMPLE_DIR / "D.V. 260 of 2024.pdf"
        if not f.exists():
            pytest.skip("Sample PDF not found")
        recs = parser.parse_document(str(f))
        assert len(recs) == 36
        
        # Verify first record
        assert recs[0].record_sequence == 1
        assert recs[0].serial_number == "1"
        assert recs[0].hearing_date == "30-05-2024"
        assert recs[0].stage == "प्रथम आदेश"
        assert "मे िपठािसन अिधकारी" in recs[0].business

        # Verify last record
        assert recs[-1].record_sequence == 36
        assert recs[-1].serial_number == "36"
        assert recs[-1].hearing_date == "22-10-2026"
        assert recs[-1].stage == "काढुन घेतला"

    def test_ma_sample_record_count(self, parser):
        f = SAMPLE_DIR / "M.A.919 of 2020.pdf"
        if not f.exists():
            pytest.skip("Sample PDF not found")
        recs = parser.parse_document(str(f))
        assert len(recs) == 67

        # Verify serial number resetting on page 3 (Rule D)
        # Rec 14 is SN 14 on page 2, Rec 15 is SN 1 on page 3
        assert recs[13].serial_number == "14"
        assert recs[13].record_sequence == 14
        assert recs[14].serial_number == "1"
        assert recs[14].record_sequence == 15
        assert recs[15].serial_number == "1"
        assert recs[15].record_sequence == 16
        
        # Verify last record
        assert recs[-1].record_sequence == 67
        assert recs[-1].serial_number == "52"
        assert recs[-1].hearing_date == "21-10-2026"
        assert recs[-1].stage == "अहवाल"

    def test_scc_sample_record_count(self, parser):
        f = SAMPLE_DIR / "S.C.C. 9311 of 2019.pdf"
        if not f.exists():
            pytest.skip("Sample PDF not found")
        recs = parser.parse_document(str(f))
        assert len(recs) == 65

        # Verify first record
        assert recs[0].record_sequence == 1
        assert recs[0].serial_number == "1"
        assert recs[0].hearing_date == "02-01-2020"
        assert recs[0].stage == "----"

        # Verify last record
        assert recs[-1].record_sequence == 65
        assert recs[-1].serial_number == "65"
        assert recs[-1].hearing_date == "23-10-2026"
        assert recs[-1].stage == "न्यायिनर्णय"

    def test_no_empty_dates_or_business(self, parser):
        for fname in ["D.V. 260 of 2024.pdf", "M.A.919 of 2020.pdf", "S.C.C. 9311 of 2019.pdf"]:
            f = SAMPLE_DIR / fname
            if not f.exists():
                continue
            recs = parser.parse_document(str(f))
            for r in recs:
                assert r.hearing_date != "", f"Empty date found in {fname} at seq {r.record_sequence}"
                assert r.business != "", f"Empty business found in {fname} at seq {r.record_sequence}"
                assert r.stage != "", f"Empty stage found in {fname} at seq {r.record_sequence}"

