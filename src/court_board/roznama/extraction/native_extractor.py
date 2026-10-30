"""
Native PDF Text and Layout Extractor using PyMuPDF (fitz).
Extracts raw text, blocks, page dimensions, and coordinates without parsing records.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
import fitz

class NativePDFExtractor:
    """
    Extracts text layers, blocks, and layout metadata from native PDF files.
    """
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"Source PDF not found at {self.pdf_path}")
        self.doc = fitz.open(str(self.pdf_path))

    @property
    def page_count(self) -> int:
        return len(self.doc)

    def extract_page_text(self, page_number: int) -> str:
        """
        Extracts raw plain text for a 1-based page index.
        """
        if page_number < 1 or page_number > len(self.doc):
            raise IndexError(f"Page number {page_number} out of bounds (1..{len(self.doc)})")
        page = self.doc[page_number - 1]
        return page.get_text()

    def extract_page_blocks(self, page_number: int) -> List[Dict[str, Any]]:
        """
        Extracts structured text blocks with coordinates (x0, y0, x1, y1, text).
        """
        if page_number < 1 or page_number > len(self.doc):
            raise IndexError(f"Page number {page_number} out of bounds")
        page = self.doc[page_number - 1]
        raw_blocks = page.get_text("blocks")
        
        blocks = []
        for b in raw_blocks:
            blocks.append({
                "bbox": (b[0], b[1], b[2], b[3]),
                "text": b[4],
                "block_no": b[5],
                "block_type": b[6]
            })
        return blocks

    def get_page_dimensions(self, page_number: int) -> tuple:
        """
        Returns (width, height) in points.
        """
        page = self.doc[page_number - 1]
        rect = page.rect
        return (rect.width, rect.height)

    def close(self):
        self.doc.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

