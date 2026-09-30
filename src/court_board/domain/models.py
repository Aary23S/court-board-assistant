from datetime import date, datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class CaseRecord(BaseModel):
    """
    Immutable domain model representing a single case from the daily board.
    Fields are named based on the actual source columns from the court extract.
    """
    source_row_index: int = Field(description="The 0-based index of the row in the source file")
    
    sr_no: Optional[str] = Field(None, description="Sr. No.")
    cases: str = Field(description="Cases (e.g. R.C.C./300267/1998)")
    party_name: Optional[str] = Field(None, description="Party Name")
    date_of_registration: Optional[str] = Field(None, description="Date of Registration")
    age: Optional[str] = Field(None, description="Age")
    ready_unready_stayed: Optional[str] = Field(None, description="Ready / Unready / Stayed")
    next_date: Optional[str] = Field(None, description="Next Date")
    next_purpose: str = Field(description="Next Purpose (Primary mapping field)")
    on_same_stage_since: Optional[str] = Field(None, description="On same Stage since")
    dormant_case_sine_die: Optional[str] = Field(None, description="DORMANT CASE/SINE DIE CASE")
    nature: Optional[str] = Field(None, description="Nature")
    delay_reason: Optional[str] = Field(None, description="Delay Reason")

    raw_values: Dict[str, Any] = Field(
        default_factory=dict,
        description="The raw cell values exactly as extracted from the source file"
    )

    class Config:
        frozen = True  # Immutable read-only collection as requested

class ValidationResult(BaseModel):
    """
    Structured validation result for a case record.
    """
    status: str = Field(description="'VALID', 'WARNING', or 'ERROR'")
    message: str
    source_row_index: Optional[int] = None
    column: Optional[str] = None
