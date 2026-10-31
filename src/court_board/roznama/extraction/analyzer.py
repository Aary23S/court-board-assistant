"""
Comprehensive Page & Document Quality Analyzer for Roznama PDFs.
Determines whether pages are native text, scanned, or mixed,
and evaluates extraction confidence.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
import re

from .native_extractor import NativePDFExtractor
from .pua_normalizer import MarathiPUANormalizer
from .ocr_engine import MarathiOCREngine
from ..domain.models import PageAnalysisResult, DocumentExtractionSummary

class PDFPageAnalyzer:
    """
    Analyzes PDF pages, performs native extraction + PUA normalization,
    and delegates to OCR when native extraction fails or is missing.
    """
    def __init__(self, ocr_engine: Optional[MarathiOCREngine] = None):
        self.normalizer = MarathiPUANormalizer()
        self.ocr_engine = ocr_engine or MarathiOCREngine()

    def analyze_document(self, pdf_path: str) -> DocumentExtractionSummary:
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        page_analyses: List[PageAnalysisResult] = []
        pages_requiring_ocr: List[int] = []
        total_pua = 0
        total_unmapped = 0
        warnings = []

        with NativePDFExtractor(str(path)) as extractor:
            total_pages = extractor.page_count

            for pno in range(1, total_pages + 1):
                width, height = extractor.get_page_dimensions(pno)
                raw_text = extractor.extract_page_text(pno)
                raw_len = len(raw_text.strip())

                pua_chars = self.normalizer.detect_pua_chars(raw_text)
                pua_count = len([c for c in raw_text if 0xE000 <= ord(c) <= 0xF8FF])
                total_pua += pua_count

                normalized_text, unmapped = self.normalizer.normalize(raw_text)
                unmapped_count = len(unmapped)
                total_unmapped += unmapped_count

                page_warnings = []
                if unmapped_count > 0:
                    page_warnings.append(f"{unmapped_count} unmapped PUA character(s) detected: {set(unmapped)}")

                # Detect suspicious/malformed sequences in raw text:
                # 1. Pre-base velanti count
                pre_base_velanti_count = len(re.findall(r'(?<![\u0915-\u0939\u094d])\u093f[\u0915-\u0939]', raw_text))
                if pre_base_velanti_count > 0:
                    page_warnings.append(f"Detected {pre_base_velanti_count} legacy pre-base velanti (U+093F) character(s); normalized to canonical Unicode.")

                # 2. Decomposed split vowels count
                split_vowel_count = len(re.findall(r'[\u0915-\u0939]\u093e\u0947', raw_text)) + len(re.findall(r'[\u0915-\u0939]\u093e\u0948', raw_text))
                if split_vowel_count > 0:
                    page_warnings.append(f"Detected {split_vowel_count} decomposed split vowel sequence(s) (U+093E+U+0947); composed to canonical Devanagari.")

                # 3. Replacement characters (U+FFFD)
                replacement_count = raw_text.count('\ufffd')
                if replacement_count > 0:
                    page_warnings.append(f"Detected {replacement_count} Unicode replacement character(s) (U+FFFD).")

                # Determine whether page is native text or scanned
                if raw_len > 100:
                    # Native text present
                    has_text = True
                    method = "NATIVE_TEXT"
                    if unmapped_count == 0:
                        quality = "EXCELLENT"
                    else:
                        quality = "ACCEPTABLE"
                elif raw_len > 0:
                    # Sparse text - possibly partial scan/text
                    has_text = True
                    method = "HYBRID"
                    quality = "UNCERTAIN"
                    page_warnings.append("Sparse text layer detected; may require OCR.")
                    pages_requiring_ocr.append(pno)
                else:
                    # Scanned page (no text layer)
                    has_text = False
                    method = "OCR"
                    pages_requiring_ocr.append(pno)
                    
                    if self.ocr_engine.is_available:
                        ocr_res = self.ocr_engine.ocr_page(str(path), pno)
                        if ocr_res["success"]:
                            normalized_text = ocr_res["text"]
                            quality = "ACCEPTABLE"
                        else:
                            quality = "FAILED"
                            page_warnings.append(f"OCR failed: {ocr_res['error']}")
                    else:
                        quality = "FAILED"
                        page_warnings.append("Page appears to be scanned but Tesseract OCR is not available.")

                analysis = PageAnalysisResult(
                    page_number=pno,
                    width=width,
                    height=height,
                    has_text_layer=has_text,
                    raw_text_length=raw_len,
                    normalized_text_length=len(normalized_text.strip()),
                    pua_count=pua_count,
                    unmapped_pua_count=unmapped_count,
                    extraction_method=method,
                    quality_status=quality,
                    warnings=page_warnings
                )
                page_analyses.append(analysis)

        # Overall summary
        methods = {a.extraction_method for a in page_analyses}
        if methods == {"NATIVE_TEXT"}:
            overall_method = "NATIVE_TEXT"
        elif methods == {"OCR"}:
            overall_method = "OCR"
        else:
            overall_method = "MIXED"

        qualities = [a.quality_status for a in page_analyses]
        if all(q == "EXCELLENT" for q in qualities):
            overall_quality = "EXCELLENT"
        elif all(q in ["EXCELLENT", "ACCEPTABLE"] for q in qualities):
            overall_quality = "ACCEPTABLE"
        elif any(q == "FAILED" for q in qualities):
            overall_quality = "FAILED"
        else:
            overall_quality = "UNCERTAIN"

        if total_unmapped > 0:
            warnings.append(f"Total unmapped PUA characters in document: {total_unmapped}")
        if pages_requiring_ocr:
            warnings.append(f"Pages requiring OCR fallback: {pages_requiring_ocr}")

        return DocumentExtractionSummary(
            filename=path.name,
            total_pages=total_pages,
            page_analyses=page_analyses,
            overall_method=overall_method,
            overall_quality=overall_quality,
            total_pua_detected=total_pua,
            total_unmapped_pua=total_unmapped,
            pages_requiring_ocr=pages_requiring_ocr,
            extraction_warnings=warnings
        )

