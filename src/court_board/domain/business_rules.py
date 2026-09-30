from typing import Optional, List
from pydantic import BaseModel, Field

class BusinessRule(BaseModel):
    """
    Explicit business rule connecting a canonical stage to its final board destination.
    """
    stage: str = Field(description="The exact canonical stage name.")
    board_section: Optional[str] = Field(None, description="The final board section ID (if APPROVED).")
    status: str = Field(description="'APPROVED', 'UNRESOLVED', 'AMBIGUOUS', 'DISABLED'")
    ready_behavior: Optional[str] = Field(None, description="'READY', 'UNREADY', 'BOTH', 'SOURCE_DRIVEN', 'NOT_APPLICABLE'")
    source: Optional[str] = Field(None, description="'OFFICER_PROVIDED', etc.")
    source_note: Optional[str] = Field(None, description="Exact provenance or note.")

class BusinessRulesConfig(BaseModel):
    rules: List[BusinessRule]
