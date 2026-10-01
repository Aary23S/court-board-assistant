import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from ..domain.business_rules import BusinessRulesConfig, BusinessRule

class BusinessRuleValidator:
    def __init__(
        self, 
        rules_path: str = "config/board_business_rules.json",
        template_path: str = "config/final_board_template.json"
    ):
        self.rules_path = Path(rules_path)
        self.template_path = Path(template_path)
        
        self.board_sections = self._load_board_sections()
        self.config = self._load_rules()

    def _load_board_sections(self) -> set:
        if not self.template_path.exists():
            return set()
        with open(self.template_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {s["name"] for s in data["sections"]}

    def _load_rules(self) -> BusinessRulesConfig:
        if not self.rules_path.exists():
            return BusinessRulesConfig(rules=[])
        with open(self.rules_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return BusinessRulesConfig(**data)

    def validate(self):
        """Validates the business rules configuration."""
        valid_statuses = {"APPROVED", "UNRESOLVED", "AMBIGUOUS", "DISABLED", "PENDING_OFFICER_DECISION"}
        
        seen_conditions = set()
        for rule in self.config.rules:
            if rule.status not in valid_statuses:
                raise ValueError(f"Invalid rule status: '{rule.status}'")
                
            if rule.status == "APPROVED" and not rule.source:
                raise ValueError(f"APPROVED rule missing provenance (source).")
                
            for dest in rule.destinations:
                if dest not in self.board_sections:
                    raise ValueError(f"Rule references unknown board section: '{dest}'")
            
            if rule.condition in seen_conditions:
                raise ValueError(f"Duplicate condition in rules: '{rule.condition}'")
            seen_conditions.add(rule.condition)
