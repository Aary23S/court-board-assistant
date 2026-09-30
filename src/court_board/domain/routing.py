from typing import Optional
from pydantic import BaseModel
from .models import CaseRecord

class BoardRoutingResult(BaseModel):
    source_case: CaseRecord
    source_row_index: int
    canonical_stage: str
    readiness_status: Optional[str]
    case_prefix: str
    board_section: Optional[str] = None
    board_row: Optional[str] = None
    routing_status: str  # ROUTED, UNRESOLVED_ROUTING, INVALID_INPUT
    routing_reason: str
