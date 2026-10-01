from typing import Optional, List
from pydantic import BaseModel

class BusinessRule(BaseModel):
    condition: str
    destinations: List[str] = []
    status: str
    source: Optional[str] = None
    source_note: Optional[str] = None

class BusinessRulesConfig(BaseModel):
    rules: List[BusinessRule]
