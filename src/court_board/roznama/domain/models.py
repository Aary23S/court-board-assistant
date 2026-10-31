"""
Domain models for Roznama Proceedings and Transformation.
"""
from typing import List, Optional
from pydantic import BaseModel, Field

class PageAnalysisResult(BaseModel):
    """
    Detailed extraction and quality metrics for a single PDF page.
    """
    page_number: int = Field(description="1-based page index")
    width: float = Field(description="Page width in points")
    height: float = Field(description="Page height in points")
    has_text_layer: bool = Field(description="Whether embedded text layer exists")
    raw_text_length: int = Field(description="Length of raw extracted text")
    normalized_text_length: int = Field(description="Length of text after PUA normalization")
    pua_count: int = Field(default=0, description="Number of PUA characters detected")
    unmapped_pua_count: int = Field(default=0, description="Number of unmapped PUA characters")
    extraction_method: str = Field(description="'NATIVE_TEXT', 'OCR', or 'HYBRID'")
    quality_status: str = Field(description="'EXCELLENT', 'ACCEPTABLE', 'UNCERTAIN', or 'FAILED'")
    warnings: List[str] = Field(default_factory=list, description="Warnings or issues encountered during extraction")

class DocumentExtractionSummary(BaseModel):
    """
    Document-level aggregation of extraction across all pages.
    """
    filename: str
    total_pages: int
    page_analyses: List[PageAnalysisResult] = Field(default_factory=list)
    overall_method: str = Field(description="'NATIVE_TEXT', 'OCR', or 'MIXED'")
    overall_quality: str = Field(description="'EXCELLENT', 'ACCEPTABLE', 'UNCERTAIN', or 'FAILED'")
    total_pua_detected: int = 0
    total_unmapped_pua: int = 0
    pages_requiring_ocr: List[int] = Field(default_factory=list)
    extraction_warnings: List[str] = Field(default_factory=list)

class SourceProceedingRecord(BaseModel):
    """
    Structured proceeding record extracted directly from source PDF.
    Preserves original sequence, serial numbers, dates, business, and stage.
    """
    record_sequence: int = Field(description="Strict 1-based sequential order in source document (Rule D)")
    serial_number: Optional[str] = Field(None, description="Original serial number from source (may repeat/reset)")
    case_number: Optional[str] = Field(None, description="Extracted case/application number")
    hearing_date: str = Field(description="Source 'दिनांक' in DD-MM-YYYY format")
    business: str = Field(description="Extracted proceedings/business description text")
    stage: str = Field(description="Extracted 'Stage:' value")
    source_page_start: int = Field(description="1-based page number where record starts")
    source_page_end: int = Field(description="1-based page number where record ends")
    raw_source_text: Optional[str] = Field(None, description="Full raw source text block for audit trail")
    normalized_source_text: Optional[str] = Field(None, description="Normalized source text block")
    extraction_method: str = Field(default="NATIVE_TEXT", description="'NATIVE_TEXT' or 'OCR'")
    extraction_confidence: float = Field(default=1.0, description="Confidence score")

class RoznamaRecord(BaseModel):
    """
    Transformed record corresponding exactly to the 3 output table columns.
    Implements Business Rules A, B, C, and D.
    """
    record_sequence: int = Field(description="Preserved source appearance order (Rule D)")
    today_date: str = Field(description="Col 1: आजची दिनांक (Mapped from source hearing_date) (Rule B)")
    proceedings_detail: str = Field(
        description="Col 2: दैनंदिन कामकाज तपशील ([Business]. Stage: [Stage]) (Rule A)"
    )
    next_date: Optional[str] = Field(
        None, 
        description="Col 3: पुढे/निकाल तारीख (Hearing date of immediately following record; None for final) (Rule C)"
    )
    judge_designation: Optional[str] = Field(
        "न्यायाधीश", 
        description="Judge / Presiding officer title placed at bottom-right of Col 2"
    )

class RoznamaHeader(BaseModel):
    """Case and court identification header metadata."""
    court_name: Optional[str] = "मुख्य न्यायदंडाधिकारी, नाशिक"
    judge_name: Optional[str] = "श्री. जे. व्ही. पालीवाल"
    case_number: Optional[str] = None
    cnr_number: Optional[str] = None
    parties: Optional[str] = None
    app_advocate: Optional[str] = None

