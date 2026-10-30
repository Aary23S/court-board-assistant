"""
State management for Roznama workflow in Streamlit.
Completely isolated from Court Board AppState.
"""
import copy
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
import re

from court_board.roznama.domain.models import (
    SourceProceedingRecord,
    RoznamaRecord,
    RoznamaHeader,
    DocumentExtractionSummary,
)
from court_board.roznama.extraction.analyzer import PDFPageAnalyzer
from court_board.roznama.parsing.record_parser import RecordBoundaryParser
from court_board.roznama.transformation.transformer import RoznamaTransformer
from court_board.roznama.rendering.pdf_renderer import RoznamaPDFRenderer

class RoznamaState:
    """
    Manages user session state, uploaded file processing, human reviews,
    manual edits, next-date overrides, and validation for Roznama PDF Generator.
    """
    def __init__(self):
        self.reset()

    def reset(self):
        """Resets all Roznama state when a new file is uploaded or cleared."""
        self.source_filename: str = ""
        self.source_file_bytes: Optional[bytes] = None
        self.source_path: Optional[str] = None
        
        self.document_summary: Optional[DocumentExtractionSummary] = None
        # Immutable original extracted records: must NEVER be mutated by human corrections
        self.original_source_records: List[SourceProceedingRecord] = []
        # Convenient alias pointing to original_source_records
        self.source_records: List[SourceProceedingRecord] = []
        
        # Transformed output records (Rule A, B, C, D)
        self.transformed_records: List[RoznamaRecord] = []
        # Original derived lookahead dates immediately after initial transformation: record_sequence -> date
        self.original_derived_next_dates: Dict[int, Optional[str]] = {}
        
        # User human-in-the-loop edits: record_sequence -> dict of corrections {"date", "business", "stage"}
        self.human_edits: Dict[int, Dict[str, Any]] = {}
        # Explicit next-date manual overrides: record_sequence -> overridden_next_date
        self.next_date_overrides: Dict[int, str] = {}
        # Records marked as reviewed by human: set of record_sequences
        self.reviewed_sequences: Set[int] = set()
        # Explicit acknowledgements for warnings (e.g., empty business/stage, OCR/uncertain pages)
        self.acknowledged_warnings: Set[str] = set()
        
        self.header_config: RoznamaHeader = RoznamaHeader()
        self.is_extracted: bool = False
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []

        # Phase 5B Generated Artifact Lifecycle Management
        self.generated_pdf_bytes: Optional[bytes] = None
        self.generated_pdf_path: Optional[str] = None
        self.generated_pdf_filename: Optional[str] = None
        self.generated_page_count: int = 0
        self.generated_record_count: int = 0
        self.generated_timestamp: Optional[str] = None
        self.generated_fingerprint: Optional[str] = None
        self.generation_error: Optional[str] = None

    def process_pdf(self, file_path: str, filename: str = "", file_bytes: bytes = None):
        """
        Runs the extraction, parsing, and transformation pipeline on an uploaded PDF.
        """
        self.reset()
        self.source_path = file_path
        self.source_filename = filename or Path(file_path).name
        self.source_file_bytes = file_bytes

        # 1. Page Analysis & Native Text / OCR Extraction Evaluation
        analyzer = PDFPageAnalyzer()
        self.document_summary = analyzer.analyze_document(file_path)

        # 2. Record Boundary Parsing
        parser = RecordBoundaryParser()
        raw_source_records = parser.parse_document(file_path)
        
        # Store deep copied immutable original records
        self.original_source_records = copy.deepcopy(raw_source_records)
        self.source_records = self.original_source_records

        # 3. Roznama Transformation (Rules A, B, C, D)
        transformer = RoznamaTransformer()
        self.transformed_records = transformer.transform(self.original_source_records)

        # Record original derived next dates to preserve audit trail
        self.original_derived_next_dates = {
            r.record_sequence: r.next_date for r in self.transformed_records
        }

        # Set default case number in header if extracted
        if self.source_records and self.source_records[0].case_number:
            self.header_config.case_number = self.source_records[0].case_number

        self.is_extracted = True
        self.validate()

    def update_record(
        self,
        record_sequence: int,
        new_date: Optional[str] = None,
        new_business: Optional[str] = None,
        new_stage: Optional[str] = None,
        manual_next_date: Optional[str] = None,
    ):
        """
        Applies a user correction to a record and re-combines proceedings detail
        strictly using the public RoznamaTransformer.format_proceedings_detail API.
        The original source records remain strictly unmodified.
        """
        if record_sequence not in self.human_edits:
            self.human_edits[record_sequence] = {}

        if new_date is not None:
            self.human_edits[record_sequence]["date"] = new_date.strip()
        if new_business is not None:
            self.human_edits[record_sequence]["business"] = new_business.strip()
        if new_stage is not None:
            self.human_edits[record_sequence]["stage"] = new_stage.strip()
        if manual_next_date is not None:
            m_val = manual_next_date.strip()
            if m_val:
                self.next_date_overrides[record_sequence] = m_val
            else:
                # If cleared, revert override to original derived date
                self.next_date_overrides.pop(record_sequence, None)

        rec_idx = next(
            (i for i, r in enumerate(self.transformed_records) if r.record_sequence == record_sequence),
            None
        )
        if rec_idx is not None:
            rec = self.transformed_records[rec_idx]
            source_rec = next(
                (s for s in self.original_source_records if s.record_sequence == record_sequence),
                None
            )

            current_b = self.human_edits[record_sequence].get("business", source_rec.business if source_rec else "")
            current_s = self.human_edits[record_sequence].get("stage", source_rec.stage if source_rec else "")
            current_d = self.human_edits[record_sequence].get("date", source_rec.hearing_date if source_rec else rec.today_date)

            rec.today_date = current_d
            # Use public RoznamaTransformer format_proceedings_detail API
            rec.proceedings_detail = RoznamaTransformer.format_proceedings_detail(current_b, current_s)

            if record_sequence in self.next_date_overrides:
                rec.next_date = self.next_date_overrides[record_sequence]
            else:
                rec.next_date = self.original_derived_next_dates.get(record_sequence)

            # If date was changed, update preceding record's lookahead next_date unless manually overridden
            if rec_idx > 0 and (self.transformed_records[rec_idx - 1].record_sequence not in self.next_date_overrides):
                self.transformed_records[rec_idx - 1].next_date = rec.today_date

        self.reviewed_sequences.add(record_sequence)
        # Any edit invalidates the previously generated PDF artifact
        self.invalidate_generated_pdf()
        self.validate()

    def mark_reviewed(self, record_sequence: int):
        self.reviewed_sequences.add(record_sequence)
        self.validate()

    def mark_all_reviewed(self):
        for r in self.transformed_records:
            self.reviewed_sequences.add(r.record_sequence)
        self.validate()

    def acknowledge_warning(self, warning_key: str):
        self.acknowledged_warnings.add(warning_key)

    def unacknowledge_warning(self, warning_key: str):
        self.acknowledged_warnings.discard(warning_key)

    def invalidate_generated_pdf(self):
        """Invalidates any generated PDF artifact when records or source inputs change."""
        self.generated_pdf_bytes = None
        if self.generated_pdf_path and Path(self.generated_pdf_path).exists():
            try:
                Path(self.generated_pdf_path).unlink(missing_ok=True)
            except Exception:
                pass
        self.generated_pdf_path = None
        self.generated_pdf_filename = None
        self.generated_page_count = 0
        self.generated_record_count = 0
        self.generated_timestamp = None
        self.generated_fingerprint = None
        self.generation_error = None

    def compute_data_fingerprint(self) -> str:
        """
        Computes a cryptographic fingerprint of all current reviewed record values and header.
        Used to strictly ensure the generated PDF corresponds to the exact current data.
        """
        import hashlib
        h = hashlib.sha256()
        h.update(self.source_filename.encode("utf-8"))
        h.update(str(self.header_config.case_number).encode("utf-8"))
        for r in self.transformed_records:
            h.update(str(r.record_sequence).encode("utf-8"))
            h.update(str(r.today_date).encode("utf-8"))
            h.update(str(r.proceedings_detail).encode("utf-8"))
            h.update(str(r.next_date).encode("utf-8"))
        return h.hexdigest()

    def generate_sanitized_filename(self) -> str:
        """
        Generates a clean, safe output PDF filename based on source filename or case number.
        Examples:
        - 'D.V. 260 of 2024.pdf' -> 'Roznama_DV_260_2024.pdf'
        - 'M.A.919 of 2020.pdf' -> 'Roznama_MA_919_2020.pdf'
        - 'S.C.C. 9311 of 2019.pdf' -> 'Roznama_SCC_9311_2019.pdf'
        """
        raw_name = self.source_filename or self.header_config.case_number or "Court_Proceeding"
        if raw_name.lower().endswith(".pdf"):
            raw_name = raw_name[:-4]

        # Convert common prefixes cleanly
        s = raw_name
        s = re.sub(r"D\.?\s*V\.?", "DV ", s, flags=re.IGNORECASE)
        s = re.sub(r"M\.?\s*A\.?", "MA ", s, flags=re.IGNORECASE)
        s = re.sub(r"S\.?\s*C\.?\s*C\.?", "SCC ", s, flags=re.IGNORECASE)
        s = re.sub(r"\bof\b", "", s, flags=re.IGNORECASE)
        # Replace non-alphanumeric chars with underscore
        clean_name = re.sub(r"[^\w\d]+", "_", s).strip("_")
        clean_name = re.sub(r"_+", "_", clean_name)
        if not clean_name:
            clean_name = "Document"
        return f"Roznama_{clean_name}.pdf"

    def is_generation_eligible(self) -> bool:
        """
        Generation eligibility gate:
        - Source PDF must be uploaded and extracted.
        - Records transformed.
        - Validation has no blocking errors.
        - All unacknowledged warnings must be resolved/acknowledged.
        - All records must be reviewed (or explicitly acknowledged).
        """
        if not self.is_extracted or not self.transformed_records:
            return False
        
        # Must pass core validation
        valid = self.validate()
        if not valid or self.validation_errors:
            return False
            
        # Must have no pending blocking warnings
        # Warnings about unreviewed records or empty fields/ocr require review or explicit acknowledgement
        if self.validation_warnings:
            # If there are unreviewed records, they must either be reviewed or acknowledged
            return False
            
        return True

    def generate_pdf(self) -> bool:
        """
        Generates the final Roznama PDF from the latest reviewed and validated records.
        Strictly integrates with RoznamaPDFRenderer.
        """
        import tempfile
        import fitz  # PyMuPDF for page count & integrity check

        self.generation_error = None

        if not self.is_generation_eligible():
            self.generation_error = "Generation gate check failed. Please resolve all validation errors and review/acknowledge all warnings."
            return False

        try:
            renderer = RoznamaPDFRenderer()
            out_filename = self.generate_sanitized_filename()
            
            # Application-managed output directory in temp
            out_dir = Path(tempfile.gettempdir()) / "roznama_generated_output"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / out_filename

            # Render records strictly using latest reviewed transformed records
            rendered_file = renderer.render(
                records=self.transformed_records,
                output_path=out_path,
                header=self.header_config
            )

            if not rendered_file.exists() or rendered_file.stat().st_size == 0:
                self.generation_error = "Rendered PDF file was not created or is 0 bytes."
                return False

            # Verify PDF integrity and retrieve page count using PyMuPDF
            doc = fitz.open(str(rendered_file))
            page_count = doc.page_count
            doc.close()

            if page_count < 1:
                self.generation_error = "Generated PDF contains 0 pages."
                return False

            # Cache artifact state
            self.generated_pdf_bytes = rendered_file.read_bytes()
            self.generated_pdf_path = str(rendered_file)
            self.generated_pdf_filename = out_filename
            self.generated_page_count = page_count
            self.generated_record_count = len(self.transformed_records)
            self.generated_timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            self.generated_fingerprint = self.compute_data_fingerprint()

            return True

        except Exception as e:
            self.generation_error = f"PDF generation error: {str(e)}"
            self.invalidate_generated_pdf()
            return False

    @staticmethod
    def is_valid_calendar_date(date_str: str) -> bool:
        """
        Validates calendar date format DD-MM-YYYY using datetime.strptime.
        Ensures valid days (e.g. leap year check, max days per month) and reasonable year.
        """
        if not date_str or not isinstance(date_str, str):
            return False
        date_str = date_str.strip()
        try:
            dt = datetime.strptime(date_str, "%d-%m-%Y")
            # Reasonable range check
            return 1900 <= dt.year <= 2100
        except ValueError:
            return False

    def validate(self) -> bool:
        """
        Runs comprehensive validation checks on all records before PDF generation.
        """
        self.validation_errors = []
        self.validation_warnings = []

        if not self.transformed_records:
            self.validation_errors.append("No records extracted from document.")
            return False

        # 1. Record count matching
        if len(self.original_source_records) != len(self.transformed_records):
            self.validation_errors.append(
                f"Record count mismatch: {len(self.original_source_records)} source records vs "
                f"{len(self.transformed_records)} transformed records."
            )

        # 2. Sequence integrity (no duplicates, strictly sequential)
        seqs = [r.record_sequence for r in self.transformed_records]
        if len(seqs) != len(set(seqs)):
            self.validation_errors.append("Duplicate record sequence numbers detected.")
        if seqs != list(range(1, len(seqs) + 1)):
            self.validation_errors.append("Record sequences are not continuous from 1 to N.")

        # 3. Calendar date validation (DD-MM-YYYY) for today_date and non-null next_date
        for r in self.transformed_records:
            if not self.is_valid_calendar_date(r.today_date):
                self.validation_errors.append(
                    f"Record #{r.record_sequence}: Invalid calendar date '{r.today_date}'. Expected valid DD-MM-YYYY."
                )
            if r.next_date is not None and not self.is_valid_calendar_date(r.next_date):
                self.validation_errors.append(
                    f"Record #{r.record_sequence}: Invalid next date '{r.next_date}'. Expected valid DD-MM-YYYY."
                )

        # 4. Empty detail check & empty business/stage acknowledgement check
        for r in self.transformed_records:
            if not r.proceedings_detail.strip():
                self.validation_errors.append(
                    f"Record #{r.record_sequence}: Proceedings detail is completely empty."
                )
            else:
                source_r = next((s for s in self.original_source_records if s.record_sequence == r.record_sequence), None)
                curr_b = self.human_edits.get(r.record_sequence, {}).get("business", source_r.business if source_r else "")
                curr_s = self.human_edits.get(r.record_sequence, {}).get("stage", source_r.stage if source_r else "")
                
                if not curr_b.strip() or not curr_s.strip():
                    warn_key = f"empty_field_rec_{r.record_sequence}"
                    missing_name = "Business (कामकाज)" if not curr_b.strip() else "Stage (स्टेज)"
                    if warn_key not in self.acknowledged_warnings:
                        self.validation_warnings.append(
                            f"Record #{r.record_sequence}: {missing_name} is empty. (Requires acknowledgement)"
                        )

        # 5. Review progress warnings
        unreviewed = len(self.transformed_records) - len(self.reviewed_sequences)
        if unreviewed > 0:
            self.validation_warnings.append(
                f"{unreviewed} record(s) have not been marked as reviewed."
            )

        # 6. Extraction warnings / OCR uncertain extractions from document analysis
        if self.document_summary:
            if self.document_summary.pages_requiring_ocr:
                warn_key = "ocr_pages_acknowledgement"
                if warn_key not in self.acknowledged_warnings:
                    self.validation_warnings.append(
                        f"Pages {self.document_summary.pages_requiring_ocr} required OCR / have uncertain quality. (Requires acknowledgement)"
                    )
            if self.document_summary.extraction_warnings:
                for w in self.document_summary.extraction_warnings:
                    self.validation_warnings.append(f"Document analysis note: {w}")

        return len(self.validation_errors) == 0

