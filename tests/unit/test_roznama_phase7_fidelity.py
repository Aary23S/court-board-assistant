"""
Comprehensive Regression Tests for Phase 7:
- Marathi Unicode fidelity (velanti reordering, split vowels, reph reordering).
- PUA consonant clusters and half-consonants preceding pre-base matras.
- Deduping accidental double vowels from ligature glyphs.
- Phase 7 Marathi Text Fidelity Validation Gate.
"""
import pytest
from court_board.roznama.extraction.pua_normalizer import MarathiPUANormalizer
from court_board.roznama.parsing.record_parser import RecordBoundaryParser
from court_board.roznama.transformation.transformer import RoznamaTransformer
from court_board.roznama.ui.roznama_state import RoznamaState
from court_board.roznama.domain.models import SourceProceedingRecord

@pytest.fixture
def normalizer():
    return MarathiPUANormalizer()

def test_phase7_specific_malformation_corrections(normalizer):
    """
    Validates that the specific malformations reported in Phase 7 are normalized accurately.
    """
    # 1. 'िफर्यादी' / 'िफया\ue77aदी' -> 'फिर्यादी'
    raw_firyadi = "िफया\ue77aदी"
    norm_firyadi, _ = normalizer.normalize(raw_firyadi)
    assert norm_firyadi == "फिर्यादी"

    # 2. 'काेिवड' / 'कोिवड' -> 'कोविड'
    raw_covid1 = "काेिवड"
    raw_covid2 = "कोिवड"
    assert normalizer.normalize(raw_covid1)[0] == "कोविड"
    assert normalizer.normalize(raw_covid2)[0] == "कोविड"

    # 3. 'प्रित िनयुक्त्◌ीवर' / 'प्रति\s+नियुक्त'
    raw_prati = "मे. कोट\ue77a \ue955ित िनयु\ue8c0त्\u25ccीवर"
    norm_prati, _ = normalizer.normalize(raw_prati)
    assert "प्रतिनियुक्तीवर" in norm_prati

    # 4. 'पीठासन अिधकारी' -> 'पीठासन अधिकारी'
    raw_adhikari = "पीठासन अिधकारी"
    assert normalizer.normalize(raw_adhikari)[0] == "पीठासन अधिकारी"

    # 5. 'िनशाणी' -> 'निशाणी'
    raw_nishani = "िनशाणी"
    assert normalizer.normalize(raw_nishani)[0] == "निशाणी"

    # 6. 'अिधक' -> 'अधिक'
    raw_adhik = "अिधक"
    assert normalizer.normalize(raw_adhik)[0] == "अधिक"

    # 7. 'िकरकोळ' -> 'किरकोळ'
    raw_kirkol = "िकरकोळ"
    assert normalizer.normalize(raw_kirkol)[0] == "किरकोळ"

    # 8. 'श्रीी.तौिफक' -> 'श्री.तौफिक'
    raw_shree = "श्रीी.तौिफक"
    assert normalizer.normalize(raw_shree)[0] == "श्री.तौफिक"

def test_phase7_pua_half_consonants_and_ligatures(normalizer):
    """
    Validates that PUA half-consonants preceding matras (e.g. \ue8c0='क्' + त)
    correctly compose into conjuncts with the matra after the full cluster (e.g. 'युक्तीवाद' / 'युक्तिवाद').
    """
    raw_yuktiwad = "Stage: िनशाणी__वर युि\ue8c0तवाद(तयार नसलेले \ue955करण)"
    norm_yuktiwad, _ = normalizer.normalize(raw_yuktiwad)
    assert "युक्तिवाद" in norm_yuktiwad or "युक्तीवाद" in norm_yuktiwad
    assert "युक्ितवाद" not in norm_yuktiwad

    raw_gram = "मे.\ue8ccयायालय ग\ue777ाम\ue8ccयायालय"
    norm_gram, _ = normalizer.normalize(raw_gram)
    assert "ग्रामन्यायालय" in norm_gram
    assert "ग्रााम" not in norm_gram

    raw_pratijna = "पुरा\ue8d5याचे \ue955ित\ue8beाप\ue954 दाखल"
    norm_pratijna, _ = normalizer.normalize(raw_pratijna)
    assert "प्रतिज्ञापत्र" in norm_pratijna
    assert "प्रतिज्ञाापत्र" not in norm_pratijna

def test_phase7_fidelity_validation_gate():
    """
    Tests RoznamaState.inspect_marathi_text_fidelity and the validation gate.
    """
    state = RoznamaState()
    
    # 1. Clean valid text produces no defects
    clean_text = "मे. न्यायालयासमक्ष फिर्यादी व वकील हजर. Stage: युक्तिवाद"
    assert state.inspect_marathi_text_fidelity(clean_text) == []

    # 2. Defective texts produce corresponding flags
    leading_short_i = "मे. कोर्ट िफर्यादी हजर"
    defects1 = state.inspect_marathi_text_fidelity(leading_short_i)
    assert any("ह्रस्व वेलांटी" in d for d in defects1)

    dotted_circle = "मे. कोर्ट\u25cc हजर"
    defects2 = state.inspect_marathi_text_fidelity(dotted_circle)
    assert any("अवैध जोडाक्षर" in d for d in defects2)

    unmapped_pua = "मे. कोर्ट \ue8ff हजर"
    defects3 = state.inspect_marathi_text_fidelity(unmapped_pua)
    assert any("रूपांतरित न झालेली अक्षरे" in d for d in defects3)

    replacement_char = "मे. कोर्ट \ufffd हजर"
    defects4 = state.inspect_marathi_text_fidelity(replacement_char)
    assert any("अज्ञात वर्ण" in d for d in defects4)

    split_vowel = "का\u0947विड"
    defects5 = state.inspect_marathi_text_fidelity(split_vowel)
    assert any("असमाविष्ट स्वर" in d for d in defects5)

    double_matra = "ग्रााम"
    defects6 = state.inspect_marathi_text_fidelity(double_matra)
    assert any("दुहेरी मात्रा" in d for d in defects6)

def test_phase7_all_source_fixtures_zero_anomalies():
    """
    Verifies that all 168 records across the 3 fixtures parse and transform
    with 0 Marathi fidelity defects.
    """
    parser = RecordBoundaryParser()
    transformer = RoznamaTransformer()
    state = RoznamaState()

    fixtures = [
        "samples/roznama/source/D.V. 260 of 2024.pdf",
        "samples/roznama/source/M.A.919 of 2020.pdf",
        "samples/roznama/source/S.C.C. 9311 of 2019.pdf",
    ]

    total_records = 0
    for f in fixtures:
        records = parser.parse_document(f)
        transformed = transformer.transform(records)
        total_records += len(transformed)

        for r in transformed:
            defects = state.inspect_marathi_text_fidelity(r.proceedings_detail)
            assert defects == [], f"Defects found in {f} Record #{r.record_sequence}: {defects}"

    assert total_records == 168
