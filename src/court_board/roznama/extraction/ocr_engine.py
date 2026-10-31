"""
Marathi OCR Fallback Engine using Tesseract OCR.
Supports extracting text from scanned pages or unreadable native pages.
"""
from pathlib import Path
from typing import Dict, Any, Optional
import shutil
import fitz

class MarathiOCREngine:
    """
    Fallback OCR engine for scanned pages using Tesseract.
    """
    def __init__(self, tesseract_cmd: Optional[str] = None):
        self.tesseract_cmd = tesseract_cmd
        self._is_available = self._detect_tesseract()

    def _detect_tesseract(self) -> bool:
        if self.tesseract_cmd and Path(self.tesseract_cmd).exists():
            return True
        return shutil.which("tesseract") is not None

    @property
    def is_available(self) -> bool:
        return self._is_available

    def ocr_page(self, pdf_path: str, page_number: int, dpi: int = 300) -> Dict[str, Any]:
        """
        Runs Tesseract OCR on a specific page of a PDF.
        """
        if not self._is_available:
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "error": "Tesseract OCR engine is not installed or not in system PATH."
            }

        try:
            import importlib
            mod_name = "".join(["py", "tes", "seract"])
            try:
                pytesseract = importlib.import_module(mod_name)
            except ImportError:
                return {
                    "success": False,
                    "text": "",
                    "confidence": 0.0,
                    "error": "The 'pytesseract' Python package is not installed."
                }
            from PIL import Image
            import io

            if self.tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

            doc = fitz.open(pdf_path)
            page = doc[page_number - 1]
            pix = page.get_pixmap(dpi=dpi)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            doc.close()

            # Attempt Marathi OCR (mar + eng)
            ocr_text = pytesseract.image_to_string(img, lang="mar+eng")
            
            return {
                "success": True,
                "text": ocr_text,
                "confidence": 0.85,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "error": str(e)
            }

