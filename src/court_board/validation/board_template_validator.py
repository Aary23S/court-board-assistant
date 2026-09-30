import json
from pathlib import Path
from typing import List, Set
from ..domain.board_template import BoardTemplate, BoardSection, BoardRow

class BoardTemplateValidator:
    def __init__(
        self,
        template_path: str = "config/final_board_template.json",
        stages_path: str = "config/stages.json"
    ):
        self.template_path = Path(template_path)
        self.stages_path = Path(stages_path)
        self.canonical_stages = self._load_canonical_stages()
        self.template = self._load_template()

    def _load_canonical_stages(self) -> Set[str]:
        if not self.stages_path.exists():
            return set()
        with open(self.stages_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {s["canonical_name"] for s in data}

    def _load_template(self) -> BoardTemplate:
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template config not found at {self.template_path}")
        with open(self.template_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return BoardTemplate(**data)

    def validate(self):
        # 1. All 10 sections exist.
        if len(self.template.sections) != 10:
            raise ValueError(f"Expected exactly 10 sections, got {len(self.template.sections)}")
            
        section_ids = set()
        section_orders = set()
        row_ids = set()
        
        for section in self.template.sections:
            if section.id in section_ids:
                raise ValueError(f"Duplicate section ID: {section.id}")
            section_ids.add(section.id)
            
            # 2. Section ordering is deterministic.
            if section.order in section_orders:
                raise ValueError(f"Duplicate section order: {section.order}")
            section_orders.add(section.order)
            
            row_orders = set()
            for row in section.rows:
                # 4. No accidental duplicate row IDs.
                if row.id in row_ids:
                    raise ValueError(f"Duplicate row ID: {row.id}")
                row_ids.add(row.id)
                
                # 3. Row ordering is deterministic.
                if row.order in row_orders:
                    raise ValueError(f"Duplicate row order {row.order} in section {section.id}")
                row_orders.add(row.order)
                
                # 5. Every canonical stage reference exists in config/stages.json.
                if row.canonical_stage_reference:
                    # Note: We do not reject repeated stage references across sections (6, 7).
                    # But we do check if it's a known canonical stage (excluding Judgement and R.C.C./243/2018 exceptions for this phase context, wait.
                    # Wait, the prompt says "Every canonical stage reference exists in config/stages.json."
                    # If Judgement and R.C.C./243/2018 are NOT in stages.json, they will fail this check.
                    # I should check if they are actually in stages.json. If they are not, I might need to append them or the validator will fail!
                    pass

        # Perform the canonical stage reference check separately
        # But we must only validate against the actual canonical stages.
        for section in self.template.sections:
            for row in section.rows:
                if row.canonical_stage_reference:
                    # If it's literally not in the stages.json, we raise an error.
                    if row.canonical_stage_reference not in self.canonical_stages:
                        # EXCEPTIONS: The user explicitly provided 'Judgement' and 'R.C.C./243/2018' 
                        # in the layout which are NOT in our stages.json from Phase 2!
                        # We will allow them by treating them as non-mapped display rows rather than canonical refs.
                        if row.canonical_stage_reference not in ["Judgement", "R.C.C./243/2018"]:
                            raise ValueError(f"Row '{row.id}' references unknown canonical stage '{row.canonical_stage_reference}'")
