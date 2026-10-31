"""
Shared presentation model for multi-format Roznama export (PDF, XLSX, DOCX).
Strictly separates data representation from renderer-specific implementations.
"""
from typing import List, Optional
from pydantic import BaseModel, Field

class HearingPresentationItem(BaseModel):
    """
    Presentation model for a single hearing section.
    Consists of:
      - Case heading: 'प्रकरण क्रमांक: [case_identification]'
      - Col 1: आजची दिनांक (Hearing Date)
      - Col 2: दैनंदिन कामकाज तपशील (Business on line 1, Stage on line 2, NO literal 'Stage:' label)
      - Col 3: पुढे/निकाल तारीख (Next Date)
      - Sequence and metadata
    """
    record_sequence: int = Field(description="1-based original sequence number")
    case_number: str = Field(default="", description="Case identification string e.g. 'फौजदारी किरकोळ अर्ज/919/2020'")
    case_heading: str = Field(description="Full repeated heading e.g. 'प्रकरण क्रमांक: ...'")
    hearing_date: str = Field(description="Col 1: आजची दिनांक (DD-MM-YYYY)")
    business_text: str = Field(default="", description="Line 1: Raw or edited business description")
    stage_text: str = Field(default="", description="Line 2: Complete stage field value without 'Stage:' label")
    combined_detail: str = Field(description="Pre-formatted 2-line detail for Col 2")
    next_date: str = Field(default="", description="Col 3: पुढे/निकाल तारीख (Blank for final record)")
    judge_designation: str = Field(default="न्यायाधीश", description="Judge designation placed at lower-right")

class RoznamaPresentationModel(BaseModel):
    """
    Collection of hearing presentation items ready for rendering.
    """
    document_case_number: str = Field(default="", description="Fallback case number from header or document")
    items: List[HearingPresentationItem] = Field(default_factory=list)

    @classmethod
    def from_state_records(
        cls,
        transformed_records,
        source_records,
        human_edits,
        header_case_number: Optional[str] = None
    ) -> "RoznamaPresentationModel":
        """
        Builds a canonical shared presentation model from state records.
        Consistently formats Business (line 1) and Stage (line 2) without 'Stage:' label.
        """
        items: List[HearingPresentationItem] = []
        doc_case_no = (header_case_number or "").strip()

        for r in transformed_records:
            seq = r.record_sequence
            src = next((s for s in source_records if s.record_sequence == seq), None)
            edits = human_edits.get(seq, {})

            # 1. Resolve case number
            c_no = ""
            if src and src.case_number and src.case_number.strip():
                c_no = src.case_number.strip()
            elif doc_case_no:
                c_no = doc_case_no

            heading = f"प्रकरण क्रमांक: {c_no}" if c_no else "प्रकरण क्रमांक:"

            # 2. Resolve business and stage
            b_val = edits.get("business", src.business if src else "")
            s_val = edits.get("stage", src.stage if src else "")

            # If not in src or edits, parse from r.proceedings_detail
            if not b_val and not s_val and r.proceedings_detail:
                detail = r.proceedings_detail
                if " Stage: " in detail:
                    parts = detail.split(" Stage: ", 1)
                    b_val = parts[0].strip()
                    s_val = parts[1].strip()
                elif detail.startswith("Stage: "):
                    b_val = ""
                    s_val = detail[len("Stage: "):].strip()
                else:
                    b_val = detail.strip()
                    s_val = ""

            b_clean = b_val.strip() if b_val else ""
            s_clean = s_val.strip() if s_val else ""

            # Line 1: Business, Line 2: Stage (never display literal 'Stage:')
            if b_clean and s_clean:
                combined = f"{b_clean}\n{s_clean}"
            elif b_clean:
                combined = b_clean
            elif s_clean:
                combined = s_clean
            else:
                combined = ""

            # 3. Next date
            nxt = r.next_date or ""

            items.append(HearingPresentationItem(
                record_sequence=seq,
                case_number=c_no,
                case_heading=heading,
                hearing_date=r.today_date,
                business_text=b_clean,
                stage_text=s_clean,
                combined_detail=combined,
                next_date=nxt,
                judge_designation=r.judge_designation or "न्यायाधीश"
            ))

        return cls(document_case_number=doc_case_no, items=items)
