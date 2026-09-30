from typing import List, Optional
from pydantic import BaseModel

class BoardRow(BaseModel):
    id: str
    display_label: str
    order: int
    canonical_stage_reference: Optional[str] = None

class BoardSection(BaseModel):
    id: str
    name: str
    order: int
    ready_unready_behavior: str
    rows: List[BoardRow]

class BoardTemplate(BaseModel):
    sections: List[BoardSection]
