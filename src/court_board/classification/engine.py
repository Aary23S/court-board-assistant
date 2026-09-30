import json
from pathlib import Path
from typing import List, Dict, Optional
from ..domain.models import CaseRecord
from .models import StageClassificationResult, StageConfig
from ..processing.normalization import normalize_next_purpose

class StageClassificationEngine:
    """
    Engine to map Next Purpose values to canonical stages.
    """
    def __init__(self, config_path: str = "config/stages.json"):
        self.stages: List[StageConfig] = []
        self._stage_map: Dict[str, str] = {}
        self._load_config(config_path)
        
    def _load_config(self, config_path: str):
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Stage configuration not found at {path}")
            
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for item in data:
            stage = StageConfig(**item)
            self.stages.append(stage)
            # Create a normalized lookup map to exact canonical names
            norm_name = normalize_next_purpose(stage.canonical_name)
            # Both lowercase and case-sensitive mappings could be used, but since Next Purpose
            # usually matches canonical stage exactly (ignoring spacing), we do a case-insensitive map.
            self._stage_map[norm_name.lower()] = stage.canonical_name

    def get_stages(self) -> List[StageConfig]:
        """Return canonical stages sorted by their configured order."""
        return sorted(self.stages, key=lambda s: s.order)

    def classify(self, record: CaseRecord) -> StageClassificationResult:
        original = record.next_purpose
        normalized = normalize_next_purpose(original)
        
        # Try to find a matching canonical stage
        canonical = self._stage_map.get(normalized.lower())
        
        status = "CLASSIFIED" if canonical else "UNMAPPED"
        
        return StageClassificationResult(
            source_case=record,
            original_next_purpose=original,
            normalized_next_purpose=normalized,
            canonical_stage=canonical,
            classification_status=status
        )
