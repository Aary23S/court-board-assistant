"""Proof of Concept: Original Source PDF Font Encoding & Character Decoder.

Diagnostic demonstration for Phase 8 investigating character code to glyph
to Unicode mapping discrepancies in court-generated PDF documents.

Scope: Diagnostic only - NOT integrated into production pipeline.
"""

from __future__ import annotations

import io
import re
import sys
from typing import Dict, List, Tuple

import fitz

# Ensure stdout handles Unicode characters on Windows console
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


class SourcePDFEncodingInspector:
    """Forensic decoder and inspector for court PDF font encodings."""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)

    def extract_tounicode_cmap(self, cmap_xref: int) -> Dict[str, Tuple[str, str]]:
        """Extract and parse a PDF /ToUnicode CMap stream.

        Returns a dictionary mapping hex character codes (e.g. '8C') to
        a tuple of (hex_unicode_string, decoded_chars).
        """
        raw_stream = self.doc.xref_stream(cmap_xref).decode("latin1", errors="replace")
        cmap_dict: Dict[str, Tuple[str, str]] = {}

        for line in raw_stream.splitlines():
            line = line.strip()
            if line.startswith("<") and ">" in line:
                parts = line.split()
                if len(parts) >= 2 and parts[0].startswith("<") and parts[1].startswith("<"):
                    src = parts[0].strip("<>").upper()
                    dst = parts[1].strip("<>").upper()
                    try:
                        dst_chars = "".join(chr(int(dst[i : i + 4], 16)) for i in range(0, len(dst), 4))
                        cmap_dict[src] = (dst, dst_chars)
                    except Exception:
                        pass
        return cmap_dict

    def dissect_hex_tokens(
        self, hex_tokens: List[str], cmap: Dict[str, Tuple[str, str]]
    ) -> List[Dict[str, str]]:
        """Dissect raw hex byte sequences through the embedded font CMap."""
        results = []
        for token in hex_tokens:
            for i in range(0, len(token), 2):
                byte_hex = token[i : i + 2].upper()
                if byte_hex in cmap:
                    dst_hex, chars = cmap[byte_hex]
                    results.append(
                        {
                            "byte": f"0x{byte_hex}",
                            "unicode_hex": f"U+{dst_hex}",
                            "char": chars,
                            "type": "PUA" if any(0xE000 <= ord(c) <= 0xF8FF for c in chars)
                            else ("Matra" if any(0x093E <= ord(c) <= 0x094F for c in chars)
                            else "Devanagari/Latin"),
                        }
                    )
                else:
                    results.append(
                        {
                            "byte": f"0x{byte_hex}",
                            "unicode_hex": "UNKNOWN",
                            "char": "?",
                            "type": "Unmapped",
                        }
                    )
        return results

    def inspect_record_evidence(self) -> None:
        """Run diagnostic comparison on key forensic cases."""
        cmap48 = self.extract_tounicode_cmap(48)
        cmap43 = self.extract_tounicode_cmap(43)

        print("=" * 80)
        print("PHASE 8 FORENSIC EVIDENCE: SOURCE PDF FONT ENCODING & CHARACTER MAPPING")
        print(f"Source PDF: {self.pdf_path}")
        print(f"Total Pages: {len(self.doc)}")
        print(f"FreeSerif CMap (xref 48) entries: {len(cmap48)}")
        print(f"FreeSerifBold CMap (xref 43) entries: {len(cmap43)}")
        print("=" * 80)

        # Case 1: Record 2 (Page 1) - Court and Firyadi
        print("\n--- CASE 1: Record 2 (07-12-2020) ---")
        tokens_rec2 = ["95", "93", "2E2088", "89", "96", "84", "8C", "97", "85", "852087", "80", "98", "84", "8C", "83", "86"]
        dissected = self.dissect_hex_tokens(tokens_rec2, cmap48)
        print(f"Extracted Byte Count: {len(dissected)}")
        print(f"{'Byte':<8} | {'Unicode':<10} | {'Char':<6} | {'Type':<15}")
        print("-" * 45)
        for d in dissected[:10]:
            print(f"{d['byte']:<8} | {d['unicode_hex']:<10} | {repr(d['char']):<6} | {d['type']:<15}")

        # Case 2: Record 14 (Page 2) - Pratiniryuktiwar
        print("\n--- CASE 2: Record 14 (14-03-2022) - 'प्रतिनियुक्तीवर' ---")
        # In stream: [<20A987>40<A12087>100<91>80<98>104 ] TJ -0.011 Ts [<9F>-104 ] TJ 0.000 Ts [<A0A1>-11<AA>11<AB869E>...
        tokens_rec14 = ["A9", "87", "A1", "87", "91", "98", "9F", "A0", "A1", "AA", "AB", "86", "9E"]
        dissected14 = self.dissect_hex_tokens(tokens_rec14, cmap48)
        print(f"{'Byte':<8} | {'Unicode':<10} | {'Char':<6} | {'Type':<15}")
        print("-" * 45)
        for d in dissected14:
            print(f"{d['byte']:<8} | {d['unicode_hex']:<10} | {repr(d['char']):<6} | {d['type']:<15}")

        # Case 3: Page 10 - Toufiq Sheikh ('श्रीी.तौफिक')
        print("\n--- CASE 3: Page 10 - 'श्रीी.तौफिक' ---")
        tokens_toufiq = ["C3", "86", "2E", "A1", "81", "87", "80", "88"]
        dissected_toufiq = self.dissect_hex_tokens(tokens_toufiq, cmap48)
        print(f"{'Byte':<8} | {'Unicode':<10} | {'Char':<6} | {'Type':<15}")
        print("-" * 45)
        for d in dissected_toufiq:
            print(f"{d['byte']:<8} | {d['unicode_hex']:<10} | {repr(d['char']):<6} | {d['type']:<15}")

        print("\n" + "=" * 80)
        print("SUMMARY FINDINGS:")
        print("1. PUA codepoints (U+E77A, U+E955, U+E8C0, U+E957) originate in PDF /ToUnicode CMap.")
        print("2. Visual layout pre-base short-i (Byte 0x87 -> U+093F) precedes consonants in content streams.")
        print("3. Duplicate vowels (Byte 0xC3 [U+E957='श्री'] followed by Byte 0x86 [U+0940='ी']) exist in source byte stream.")
        print("4. Therefore, source text corruption occurs at PDF generation time in court CIS software.")
        print("=" * 80)


if __name__ == "__main__":
    inspector = SourcePDFEncodingInspector("samples/roznama/source/M.A.919 of 2020.pdf")
    inspector.inspect_record_evidence()

