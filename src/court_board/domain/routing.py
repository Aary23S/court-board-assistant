from typing import Optional, List
from pydantic import BaseModel
from .models import CaseRecord

class BoardDestination(BaseModel):
    section_id: str
    section_name: str
    row_id: Optional[str] = None
    row_name: Optional[str] = None
    source_stage: str
    routing_reason: str

class BoardRoutingResult(BaseModel):
    source_case: CaseRecord
    source_row_index: int
    canonical_stage: str
    readiness_status: Optional[str]
    case_prefix: str
    destinations: List[BoardDestination] = []
    routing_status: str  # ROUTED, UNRESOLVED_ROUTING, INVALID_INPUT
    routing_reason: str
