from typing import Optional
from pydantic import BaseModel, Field
from ..domain.models import CaseRecord

class StageClassificationResult(BaseModel):
    """
    Result of mapping a case's Next Purpose to a canonical stage.
    """
    source_case: CaseRecord
    original_next_purpose: str
    normalized_next_purpose: str
    canonical_stage: Optional[str]
    classification_status: str = Field(description="'CLASSIFIED' or 'UNMAPPED'")

class StageConfig(BaseModel):
    """
    Configuration definition for a canonical stage.
    """
    canonical_name: str
    order: int
