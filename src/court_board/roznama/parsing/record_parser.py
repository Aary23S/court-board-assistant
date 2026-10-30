"""
Record Boundary Parser for Maharashtra Court Proceedings PDFs.
Extracts structured SourceProceedingRecord objects from normalized page text.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
import re
import fitz

from ..extraction.pua_normalizer import MarathiPUANormalizer
from ..domain.models import SourceProceedingRecord

class RecordBoundaryParser:
    """
    Parses normalized PDF pages into structured SourceProceedingRecord objects.
    Preserves exact appearance order, multiline business, and raw text.
    """
    def __init__(self, normalizer: Optional[MarathiPUANormalizer] = None):
        self.normalizer = normalizer or MarathiPUANormalizer()

    def parse_document(self, pdf_path: str) -> List[SourceProceedingRecord]:
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found at: {path}")

        doc = fitz.open(str(path))
        records: List[SourceProceedingRecord] = []
        global_sequence = 0

        for pno in range(len(doc)):
            raw_page_text = doc[pno].get_text()
            norm_page_text, _ = self.normalizer.normalize(raw_page_text)

            # Split page text by 'Party Name:' anchor
            party_parts = norm_page_text.split("Party Name:")
            raw_party_parts = raw_page_text.split("Party Name:")
            
            if len(party_parts) <= 1:
                continue

            for i in range(len(party_parts) - 1):
                global_sequence += 1
                header_chunk = party_parts[i]
                body_chunk = party_parts[i + 1]
                
                raw_header = raw_party_parts[i] if i < len(raw_party_parts) else ""
                raw_body = raw_party_parts[i + 1] if i + 1 < len(raw_party_parts) else ""

                # 1. Date: Find the hearing date (DD-MM-YYYY) right before 'Party Name:'
                dates = re.findall(r"\b(\d{2}-\d{2}-\d{4})\b", header_chunk)
                h_date = dates[-1] if dates else ""

                # 2. Serial Number & Case Number:
                sub_stage_idx = header_chunk.rfind("Sub Stage:")
                if sub_stage_idx != -1:
                    meta_chunk = header_chunk[sub_stage_idx:]
                    first_nl = meta_chunk.find("\n")
                    if first_nl != -1:
                        meta_chunk = meta_chunk[first_nl + 1:]
                else:
                    # First record on page - look after page indicator (e.g. '1/9', '3/11')
                    # Look after 'कामकाज' table header if present, or match the last \d+/\d+ in header
                    page_matches = list(re.finditer(r"\b\d{1,2}/\d{1,2}\b", header_chunk))
                    if page_matches:
                        meta_chunk = header_chunk[page_matches[-1].end():]
                    elif "कामकाज" in header_chunk:
                        meta_chunk = header_chunk[header_chunk.find("कामकाज") + len("कामकाज"):]
                    else:
                        meta_chunk = header_chunk

                # Isolate serial number (integer at start of line or before case name)
                sn_matches = re.findall(r"(?:^|\n)\s*(\d{1,3})\s*(?:\n|[^\d\n])", meta_chunk)
                sn = sn_matches[0] if sn_matches else ""

                # Extract case number between SN and Date
                case_no = ""
                if h_date and h_date in meta_chunk:
                    case_raw = meta_chunk[:meta_chunk.rfind(h_date)]
                    case_raw = case_raw.strip()
                    if sn and case_raw.startswith(sn):
                        case_raw = case_raw[len(sn):].strip()
                    case_no = " ".join(case_raw.split()).strip()

                # 3. Business: text between 'Business:' and 'Exhibit:' in body_chunk
                b_start = body_chunk.find("Business:")
                e_start = body_chunk.find("Exhibit:")
                if b_start != -1 and e_start != -1:
                    bus_text = body_chunk[b_start + len("Business:"):e_start]
                    business = " ".join(bus_text.split()).strip()
                else:
                    business = ""

                # 4. Stage: text between 'Stage:' and 'Sub Stage:'
                stg_start = body_chunk.find("Stage:")
                sub_start = body_chunk.find("Sub Stage:")
                if stg_start != -1 and sub_start != -1:
                    stg_text = body_chunk[stg_start + len("Stage:"):sub_start]
                    stage = " ".join(stg_text.split()).strip()
                else:
                    stage = ""

                record = SourceProceedingRecord(
                    record_sequence=global_sequence,
                    serial_number=sn,
                    case_number=case_no,
                    hearing_date=h_date,
                    business=business,
                    stage=stage,
                    source_page_start=pno + 1,
                    source_page_end=pno + 1,
                    raw_source_text=raw_header[-200:] + "Party Name:" + raw_body[:300],
                    normalized_source_text=header_chunk[-200:] + "Party Name:" + body_chunk[:300],
                    extraction_method="NATIVE_TEXT",
                    extraction_confidence=1.0
                )
                records.append(record)

        doc.close()
        return records
