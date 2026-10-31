"""
Phase 7 Diagnostic and Verification Utility.
Inspects all 168 records across the three fixture source documents:
- samples/roznama/source/D.V. 260 of 2024.pdf (36 records)
- samples/roznama/source/M.A.919 of 2020.pdf (67 records)
- samples/roznama/source/S.C.C. 9311 of 2019.pdf (65 records)

Captures:
- Raw extracted text
- PUA normalized text
- Unicode normalized text
- Parsed business/stage text
- Final transformed proceedings detail
- Suspicious codepoints and anomalies
"""
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

from court_board.roznama.extraction.pua_normalizer import MarathiPUANormalizer
from court_board.roznama.parsing.record_parser import RecordBoundaryParser
from court_board.roznama.transformation.transformer import RoznamaTransformer

SOURCE_FILES = [
    "samples/roznama/source/D.V. 260 of 2024.pdf",
    "samples/roznama/source/M.A.919 of 2020.pdf",
    "samples/roznama/source/S.C.C. 9311 of 2019.pdf",
]

# Patterns for detecting suspicious sequences in Devanagari text
SUSPICIOUS_PATTERNS = {
    "leading_orphaned_short_i": re.compile(r"(?:^|[\s\(\[\{\"'`।॥])\u093F"),
    "unmapped_pua": re.compile(r"[\uE000-\uF8FF]"),
    "dotted_circle": re.compile(r"\u25CC"),
    "replacement_char": re.compile(r"\uFFFD"),
    "split_vowel_o": re.compile(r"[\u0915-\u0939]\u093C?\u093E\u0947"),
    "split_vowel_au": re.compile(r"[\u0915-\u0939]\u093C?\u093E\u0948"),
    "double_virama": re.compile(r"\u094D\u094D"),
    "double_ee_matra": re.compile(r"\u0940\u0940"),
    "double_aa_matra": re.compile(r"\u093E\u093E"),
    "virama_then_matra": re.compile(r"\u094D[\u093E-\u094C]"),
}

SPECIFIC_PHASE7_TARGETS = [
    "िफर्यादी",
    "काेिवड",
    "कोिवड",
    "प्रित िनयुक्त्◌ीवर",
    "प्रित नियुक्त्◌ीवर",
    "पीठासन अिधकारी",
    "िनशाणी",
    "अिधक",
    "िकरकोळ",
    "श्रीी",
    "तौिफक",
]

def analyze_text_for_defects(text: str) -> Dict[str, List[str]]:
    defects = {}
    for name, pat in SUSPICIOUS_PATTERNS.items():
        matches = pat.findall(text)
        if matches:
            defects[name] = matches
    return defects

def run_diagnostic():
    parser = RecordBoundaryParser()
    transformer = RoznamaTransformer()
    normalizer = MarathiPUANormalizer()

    total_records = 0
    all_findings = []

    print(f"=== ROZNAMA PHASE 7 MARATHI FIDELITY DIAGNOSTIC ===")

    for src in SOURCE_FILES:
        path = Path(src)
        if not path.exists():
            print(f"ERROR: {src} not found!")
            continue

        records = parser.parse_document(str(path))
        transformed = transformer.transform(records)
        print(f"\nProcessing {path.name}: {len(records)} parsed, {len(transformed)} transformed")
        total_records += len(records)

        for i, (rec, trans) in enumerate(zip(records, transformed), start=1):
            # Check raw vs normalized vs transformed
            raw_text = rec.raw_source_text
            proc_text = trans.proceedings_detail

            # Scan raw for Phase 7 targets
            target_hits_raw = [t for t in SPECIFIC_PHASE7_TARGETS if t in raw_text]
            target_hits_proc = [t for t in SPECIFIC_PHASE7_TARGETS if t in proc_text]

            # Detect suspicious Unicode artifacts in transformed text
            defects_proc = analyze_text_for_defects(proc_text)

            if target_hits_proc or defects_proc:
                print(f"  [Record {rec.record_sequence} | Hearing: {trans.today_date}]")
                if target_hits_proc:
                    print(f"    WARNING: Target hit in transformed: {target_hits_proc}")
                if defects_proc:
                    print(f"    WARNING: Suspicious codepoints in transformed: {defects_proc}")
                print(f"    Proceedings: {proc_text[:120]}...")

    print(f"\nTotal Records Checked: {total_records} / 168")

if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    run_diagnostic()
