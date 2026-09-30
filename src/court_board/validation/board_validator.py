import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, ValidationError

class BoardSectionConfig(BaseModel):
    id: str
    name: str
    order: int
    ready_unready_behavior: str
    stages: List[str]

class BoardLayoutConfig(BaseModel):
    sections: List[BoardSectionConfig]

class BoardValidator:
    def __init__(self, stages_config_path: str = "config/stages.json", board_config_path: str = "config/board_layout.json"):
        self.stages_config_path = Path(stages_config_path)
        self.board_config_path = Path(board_config_path)
        self.canonical_stages = self._load_canonical_stages()
        self.layout: BoardLayoutConfig = self._load_layout()
        
    def _load_canonical_stages(self) -> List[str]:
        if not self.stages_config_path.exists():
            return []
        with open(self.stages_config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [s["canonical_name"] for s in data]

    def _load_layout(self) -> BoardLayoutConfig:
        if not self.board_config_path.exists():
            raise FileNotFoundError(f"Board layout config not found at {self.board_config_path}")
        with open(self.board_config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return BoardLayoutConfig(**data)
            
    def validate_structure(self):
        """Validates structural integrity of the board configuration."""
        section_ids = set()
        section_orders = set()
        
        for section in self.layout.sections:
            if not section.name:
                raise ValueError(f"Section {section.id} has no name.")
            if section.id in section_ids:
                raise ValueError(f"Duplicate section ID: {section.id}")
            section_ids.add(section.id)
            
            if section.order in section_orders:
                raise ValueError(f"Duplicate section order: {section.order}")
            section_orders.add(section.order)
            
            for stage in section.stages:
                if stage not in self.canonical_stages:
                    raise ValueError(f"Section '{section.id}' references non-existent canonical stage: '{stage}'")

    def determine_stage_mappings(self) -> Dict[str, Dict[str, Any]]:
        """
        Maps every canonical stage to its final board status.
        Returns Dict[stage_name] = {"status": str, "sections": List[str]}
        Statuses: UNIQUE, AMBIGUOUS, UNRESOLVED, NOT_ON_FINAL_BOARD
        """
        # Build inverse map: stage -> list of sections
        stage_to_sections = {stage: [] for stage in self.canonical_stages}
        
        for section in self.layout.sections:
            for stage in set(section.stages):  # Ignore accidental duplicates in the same section array
                if stage in stage_to_sections:
                    stage_to_sections[stage].append(section.name)
                    
        results = {}
        for stage in self.canonical_stages:
            sections = stage_to_sections[stage]
            
            if len(sections) == 1:
                status = "UNIQUE"
            elif len(sections) > 1:
                status = "AMBIGUOUS"
            else:
                # The instructions say: "If the reference does not establish that Stage X -> Section Y, do NOT guess. Mark it as UNRESOLVED."
                # Wait, "A stage that is not present on the final board is not necessarily an error... NOT_ON_FINAL_BOARD."
                # How do we distinguish UNRESOLVED from NOT_ON_FINAL_BOARD? 
                # If we have no business rule mapping it, it's UNRESOLVED (needs business rule).
                # NOT_ON_FINAL_BOARD is a conscious business rule decision. Since we have no rules yet, they are UNRESOLVED.
                status = "UNRESOLVED"
                
            results[stage] = {
                "status": status,
                "sections": sections
            }
            
        return results
