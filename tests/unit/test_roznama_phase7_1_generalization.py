"""
Phase 7.1 Comprehensive Generalization, Idempotency, and Adversarial Test Suite.
Tests:
  - Task 1 & 2: General Devanagari character set preservation across independent vowels,
    consonants, dependent vowel signs (matras), conjuncts, reph, rakar, half-consonants,
    anusvara, visarga, nukta, numerals, legal terminology, mixed Marathi/English.
  - Task 3: Idempotency across the entire corpus: normalize(normalize(text)) == normalize(text).
    Preservation of numbers, punctuation, English, valid conjuncts, and immutable raw text.
  - Task 4: Adversarial validation tests: precision, recall, false-positive & false-negative checks.
"""
import pytest
import re
from court_board.roznama.extraction.pua_normalizer import MarathiPUANormalizer, MARATHI_PUA_GLYPH_MAP
from court_board.roznama.ui.roznama_state import RoznamaState
from court_board.roznama.domain.models import SourceProceedingRecord, RoznamaRecord
from court_board.roznama.transformation.transformer import RoznamaTransformer

@pytest.fixture
def normalizer():
    return MarathiPUANormalizer()

@pytest.fixture
def state():
    return RoznamaState()

# Independent linguistic corpus of valid Devanagari constructs
GENERAL_DEVANAGARI_CORPUS = [
    # 1. Independent Vowels
    "अ आ इ ई उ ऊ ऋ ए ऐ ओ औ अं अः",
    # 2. Consonants
    "क ख ग घ ङ च छ ज झ ञ ट ठ ड ढ ण त थ द ध न प फ ब भ म य र ल व श ष स ह ळ क्ष ज्ञ",
    # 3. Dependent Vowel Signs (Matras on क)
    "का कि की कु कू कृ के कै को कौ कं कः",
    # 4. Complex Conjuncts & Ligatures
    "अर्क, मूर्ख, मार्ग, दीर्घ, खर्च, अर्ज, कोर्ट, अर्थ, संदर्भ, सर्व, वर्ष, स्पर्श, गार्हस्थ्य", # Reph
    "प्रकाश, क्रम, ग्राम, तीव्र, भ्रम, राष्ट्र, ट्रेन, ड्रम, स्रष्टा, सहस्त्र", # Rakar
    "सत्य, न्याय, मुख्य, संक्षिप्त, प्रसिद्ध, बुद्ध, त्याग, ध्यान, प्याला, लग्न, शब्द, स्तब्ध", # Conjuncts
    "चिन्ह, अपराह्‍ण, प्रल्हाद, ब्रम्ह, बाह्य, आल्हाद", # Ha-ligatures
    "कल्याण, म्हैसूर, उन्हाळा, कुऱ्हाड, विहीर", # Marathi specific conjuncts
    # 5. Anusvara, Visarga, Nukta
    "अंधार, निबंध, संबंध, रंग, शंका, दुःख, अंतःकरण, स्वतः, कागद, अर्ज, पोलीस, झेरॉक्स, रफ",
    # 6. Marathi Numerals & Dates
    "० १ २ ३ ४ ५ ६ ७ ८ ९",
    "दिनांक २५-०३-२०२५ रोजी रक्कम रु. १०,०००/- भरण्यात आली.",
    # 7. Legal Terminology & Mixed English
    "मे. १ल्या सह दिवाणी न्यायाधीश कनिष्ठ स्तर तथा जे.एम.एफ.सी., नाशिक",
    "फौजदारी किरकोळ अर्ज क्र. ९१९/२०२० अन्वये मे. कोर्टात हजर.",
    "Order Passed: Issue Non-Bailable Warrant (NBW) against accused under Section 138 of N.I. Act.",
    "Applicant present with advocate; Respondent absent. Adjourned for Say.",
    "Exhibit No. 14 — D.W. Warrant returned unserved. Report filed by Police Station.",
]

def test_task2_general_devanagari_corpus_preservation(normalizer):
    """
    Verifies that all standard, already-correct Devanagari text remains completely unmodified.
    """
    for sample in GENERAL_DEVANAGARI_CORPUS:
        normalized, unmapped = normalizer.normalize(sample)
        assert normalized == sample, f"Preservation failed for: '{sample}' -> '{normalized}'"
        assert unmapped == [], f"Unexpected unmapped PUA in clean text: {unmapped}"

def test_task3_idempotency_across_corpus(normalizer):
    """
    Verifies that normalization is strictly idempotent across both clean and transformed text:
    normalize(normalize(text)) == normalize(text).
    """
    # Test on corpus
    for sample in GENERAL_DEVANAGARI_CORPUS:
        step1, _ = normalizer.normalize(sample)
        step2, _ = normalizer.normalize(step1)
        assert step2 == step1, f"Idempotency failed on clean text: '{step1}' != '{step2}'"

    # Test on legacy/corrupted inputs
    legacy_samples = [
        "Business: मे. कोटा\ue77aसमोरर िफया\ue77aदी गैरहजर आरोपी गैरहजर",
        "Business: मे. कोट\ue77a \ue955ित िनयु\ue8c0त्◌ीवर अज\ue77aदार हजर",
        "Stage: िनशाणी__वर युि\ue8c0तवाद(तयार नसलेले \ue955करण)",
        "Business: मे.\ue8ccयायालय ग\ue777ाम\ue8ccयायालय हरसुल येथे मे.\ue955भारी",
        "Business: मा. \ue955मुख िज\ue8d3हा व स\ue954 \ue8ccयायाधीश सााे., नािशक यांचे आदेश",
        "हजर िन १२ िफया\ue77aदीतफ\ue76f पुरा\ue8d5याचे \ue955ित\ue8beाप\ue954 दाखल",
        "काेिवड संसर्ग आणि कोिवड - १९",
        "श्रीी.तौिफक आणि अिधकारी",
    ]
    for leg in legacy_samples:
        step1, _ = normalizer.normalize(leg)
        step2, _ = normalizer.normalize(step1)
        assert step2 == step1, f"Idempotency failed on transformed text: '{step1}' != '{step2}'"

def test_task3_preservation_of_numbers_punctuation_and_english(normalizer):
    """
    Verifies that ASCII numbers, Marathi numbers, punctuation, legal symbols,
    and English case terminology are preserved identically.
    """
    text = "R.C.C./101/2026 at 11:30 AM (Rs. 1,27,500/-) [Sec. 138, N.I. Act] - Issue summons!"
    norm, unmapped = normalizer.normalize(text)
    assert norm == text
    assert unmapped == []

def test_task4_adversarial_validation_gate(state):
    """
    Adversarial validation test suite covering all defect categories:
    Measures Precision, Recall, False Positives (FP), and False Negatives (FN).
    """
    adversarial_dataset = [
        # (ID, Text, ExpectedDefective, DefectCategorySubstr)
        # --- VALID TEXTS (ExpectedDefective = False) ---
        ("V1", "मे. न्यायालयासमक्ष फिर्यादी व वकील हजर.", False, None),
        ("V2", "Order Passed: Case adjourned for cross-examination.", False, None),
        ("V3", "दिनांक ०६-११-२०२० रोजी कामकाज झाले.", False, None),
        ("V4", "सर्वोच्च न्यायालय व उच्च न्यायालय यांचे निर्णय.", False, None),
        ("V5", "प्रकरण क्रमांक १२३/२०२४ प्रमाणे (अर्ज क्र. १५).", False, None),
        ("V6", "न्यायदंडाधिकारी, जिल्हा व सत्र न्यायालय, वरिष्ठ स्तर.", False, None),
        ("V7", "अंधार, निबंध, संबंध, रंग, शंका, दुःख, स्वतः.", False, None),
        ("V8", "कागदपत्र, झेरॉक्स, पोलीस, हजर.", False, None),
        ("V9", "Stage: युक्तिवाद (तयार नसलेले प्रकरण)", False, None),
        ("V10", "D.W. Warrant issued on 25-03-2025; returned served.", False, None),

        # --- MALFORMED TEXTS (ExpectedDefective = True) ---
        # 1. Leading / orphaned short-i
        ("M1", "मे. कोर्ट िफर्यादी गैरहजर.", True, "ह्रस्व वेलांटी"),
        ("M2", "िबन जमानती वॉरंट.", True, "ह्रस्व वेलांटी"),
        ("M3", "कामासाठी (िहं.का.अज) दाखल.", True, "ह्रस्व वेलांटी"),

        # 2. Dotted circle artifact
        ("M4", "मे. कोर्ट\u25CC हजर.", True, "अवैध जोडाक्षर"),
        ("M5", "न्यायालयात\u25CC युक्तिवाद.", True, "अवैध जोडाक्षर"),

        # 3. Unmapped PUA codepoints
        ("M6", "अज\uE8FFदार हजर.", True, "रूपांतरित न झालेली अक्षरे"),
        ("M7", "मे. \uF001यायालय.", True, "रूपांतरित न झालेली अक्षरे"),
        ("M8", "वकील \uF777 हजर.", True, "रूपांतरित न झालेली अक्षरे"),

        # 4. Replacement character
        ("M9", "अर्जदाराचे \uFFFD म्हणणे.", True, "अज्ञात वर्ण"),
        ("M10", "\uFFFDयायाधीश हजर.", True, "अज्ञात वर्ण"),

        # 5. Split vowels
        ("M11", "का\u0947विड संसर्ग.", True, "असमाविष्ट स्वर"),
        ("M12", "प\u093E\u0948कार हजर.", True, "असमाविष्ट स्वर"),
        ("M13", "समाेराेपी गैरहजर.", True, "असमाविष्ट स्वर"),

        # 6. Virama directly followed by vowel matra
        ("M14", "युक्ितवाद ऐकण्यात आला.", True, "हलंत विसंगती"),
        ("M15", "न्याय्य्ाधीश हजर.", True, "हलंत विसंगती"),
        ("M16", "प्रकरणातत्े आदेश.", True, "हलंत विसंगती"),

        # 7. Accidental double vowel matra
        ("M17", "ग्राामन्यायालय हरसुल.", True, "दुहेरी मात्रा"),
        ("M18", "श्रीी. जे. व्ही. पालीवाल.", True, "दुहेरी मात्रा"),
        ("M19", "द्वाारे पैसे भरले.", True, "दुहेरी मात्रा"),
        ("M20", "सााे., नाशिक.", True, "दुहेरी मात्रा"),
    ]

    tp = 0
    fp = 0
    tn = 0
    fn = 0

    for sample_id, text, expected_defective, defect_sub in adversarial_dataset:
        defects = state.inspect_marathi_text_fidelity(text)
        is_flagged = len(defects) > 0

        if expected_defective:
            if is_flagged and (defect_sub is None or any(defect_sub in d for d in defects)):
                tp += 1
            else:
                fn += 1
                pytest.fail(f"False Negative for {sample_id}: '{text}' expected '{defect_sub}', got {defects}")
        else:
            if not is_flagged:
                tn += 1
            else:
                fp += 1
                pytest.fail(f"False Positive for {sample_id}: '{text}' flagged with {defects}")

    total = len(adversarial_dataset)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    accuracy = (tp + tn) / total

    assert precision == 1.0
    assert recall == 1.0
    assert accuracy == 1.0
    assert fp == 0
    assert fn == 0
