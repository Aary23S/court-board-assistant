"""
Unit tests for Phase 9 Controlled Integration of Verified CIS Marathi Glyph Corrections.
Validates:
1. PUA mappings: U+E8C8 -> ण्, U+E8C9 -> त्, U+E8D5 -> व्, U+E76F -> ेर् (Reph sequence).
2. Systematic Marathi sequence reconstruction: 'ऐकण्यात', 'त्यांना', 'पुराव्या', 'तर्फे'.
3. Category C audit events: detection, explicit operator review, blocking and unblocking.
4. Approval invalidation on subsequent edit.
5. Idempotency and preservation of valid Devanagari text.
"""
import pytest
from pathlib import Path
from court_board.roznama.extraction.pua_normalizer import MarathiPUANormalizer, MARATHI_PUA_GLYPH_MAP
from court_board.roznama.ui.roznama_state import RoznamaState
from court_board.roznama.parsing.record_parser import RecordBoundaryParser

SAMPLE_DIR = Path("samples/roznama/source")

class TestPhase9ControlledIntegration:
    @pytest.fixture
    def normalizer(self):
        return MarathiPUANormalizer()

    @pytest.fixture
    def state(self):
        return RoznamaState()

    def test_verified_pua_mappings_in_dictionary(self, normalizer):
        """Task 1 & 2: Verify corrected half-consonant and Reph glyph mappings."""
        assert normalizer.mapping['\ue8c8'] == 'ण्'
        assert normalizer.mapping['\ue8c9'] == 'त्'
        assert normalizer.mapping['\ue8d5'] == 'व्'
        assert normalizer.mapping['\ue76f'] == 'ेर्'

    def test_sequence_reconstruction_half_consonants(self, normalizer):
        """Verify that half-consonants correctly form Devanagari conjuncts with virama."""
        # \ue8c8 -> ण् + या + त -> ण्यात (e.g. ऐक\ue8c8यात -> ऐकण्यात)
        norm, _ = normalizer.normalize("ऐक\ue8c8यात")
        assert norm == "ऐकण्यात"

        # \ue8c8 in वगळ\ue8c8यात -> वगळण्यात
        norm, _ = normalizer.normalize("वगळ\ue8c8यात")
        assert norm == "वगळण्यात"

        # \ue8c9 -> त् + यां + ना -> त्यांना
        norm, _ = normalizer.normalize("\ue8c9यांना \ue8c9यांचे")
        assert norm == "त्यांना त्यांचे"

        # \ue8d5 -> व् + या + चे -> पुराव्याचे
        norm, _ = normalizer.normalize("पुरा\ue8d5याचे")
        assert norm == "पुराव्याचे"

    def test_reph_reordering_with_e76f(self, normalizer):
        """Verify composite Reph and E-matra handling (तफ\ue76f -> तर्फे)."""
        norm, _ = normalizer.normalize("आरोपीतफ\ue76f")
        assert norm == "आरोपीतर्फे"

        norm, _ = normalizer.normalize("अज\ue77aदारातफ\ue76f")
        assert norm == "अर्जदारातर्फे"

    def test_idempotency_and_clean_preservation(self, normalizer):
        """Ensure already-correct Marathi text is not modified and repeated passes are identical."""
        samples = [
            "युक्तीवाद ऐकण्यात आला.",
            "त्यांना त्यांचे अधिकार देण्यात आले.",
            "पुराव्याचे प्रतिज्ञापत्र दाखल.",
            "अर्जदारातर्फे वकीलांचा युक्तीवाद.",
            "आरोपीतर्फे वकील हजर.",
            "फिर्यादीतर्फे वकील गैरहजर.",
        ]
        for s in samples:
            pass1, _ = normalizer.normalize(s)
            assert pass1 == s, f"Pass 1 modified valid text: {s} -> {pass1}"
            pass2, _ = normalizer.normalize(pass1)
            assert pass2 == pass1, f"Normalization not idempotent: {pass1} -> {pass2}"

    def test_category_c_detection_and_blocking_gate(self, state):
        """Verify Category C detection blocks generation until explicit operator approval."""
        ma_path = SAMPLE_DIR / "M.A.919 of 2020.pdf"
        if not ma_path.exists():
            pytest.skip("Fixture not available")

        state.process_pdf(str(ma_path), filename="M.A.919 of 2020.pdf")
        assert len(state.transformed_records) == 67

        # Category C events must be detected
        assert len(state.category_c_events) > 0
        assert 14 in state.category_c_events or 15 in state.category_c_events
        assert 57 in state.category_c_events
        assert 59 in state.category_c_events

        state.mark_all_reviewed()
        # With unapproved Category C events, generation must be blocked!
        assert state.has_unapproved_category_c_events() is True
        assert state.is_generation_eligible() is False

        # Approve all Category C events
        state.approve_all_category_c_events()
        assert state.has_unapproved_category_c_events() is False
        assert state.is_generation_eligible() is True

    def test_category_c_approval_invalidation_on_edit(self, state):
        """Verify that editing a record invalidates its Category C approval."""
        ma_path = SAMPLE_DIR / "M.A.919 of 2020.pdf"
        if not ma_path.exists():
            pytest.skip("Fixture not available")

        state.process_pdf(str(ma_path), filename="M.A.919 of 2020.pdf")
        state.mark_all_reviewed()
        state.approve_all_category_c_events()
        assert state.is_generation_eligible() is True

        # Human edits record 57
        state.update_record(record_sequence=57, new_business="सुनावणी पुढे ढकलली.")
        # Approval for record 57 is invalidated
        assert 57 not in state.approved_category_c_events
        # Check generation eligibility
        assert state.is_generation_eligible() is True  # new text no longer has Category C events!

