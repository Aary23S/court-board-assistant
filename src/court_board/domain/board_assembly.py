from typing import List, Optional
from pydantic import BaseModel
from .routing import BoardDestination

class FinalBoardEntry(BaseModel):
    case_number: str
    party_name: str
    source_row_number: int

    registration_date: str
    age: str
    readiness_status: str
    next_date: str
    next_purpose: str
    canonical_stage: str
    on_same_stage_since: str
    dormant_status: str
    nature: str
    delay_reason: str

    routing_reason: str

    source_destination: BoardDestination
    optional_row_id: Optional[str] = None
    optional_row_name: Optional[str] = None

class FinalBoardSection(BaseModel):
    section_id: str
    section_name: str
    order: int
    entries: List[FinalBoardEntry] = []

class FinalBoard(BaseModel):
    date: str
    sections: List[FinalBoardSection] = []
