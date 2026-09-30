import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from ..domain.business_rules import BusinessRulesConfig, BusinessRule

class BusinessRuleValidator:
    def __init__(
        self, 
        rules_path: str = "config/board_business_rules.json",
        stages_path: str = "config/stages.json",
        board_path: str = "config/board_layout.json"
    ):
        self.rules_path = Path(rules_path)
        self.stages_path = Path(stages_path)
        self.board_path = Path(board_path)
        
        self.canonical_stages = self._load_canonical_stages()
        self.board_sections = self._load_board_sections()
        self.config = self._load_rules()
        
    def _load_canonical_stages(self) -> set:
        if not self.stages_path.exists():
            return set()
        with open(self.stages_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {s["canonical_name"] for s in data}

    def _load_board_sections(self) -> set:
        if not self.board_path.exists():
            return set()
        with open(self.board_path, 'r', encoding='utf-8') as f:
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
        seen_stages = {}
        valid_statuses = {"APPROVED", "UNRESOLVED", "AMBIGUOUS", "DISABLED"}
        valid_ready = {"READY", "UNREADY", "BOTH", "SOURCE_DRIVEN", "NOT_APPLICABLE", None}
        
        for rule in self.config.rules:
            if rule.stage not in self.canonical_stages:
                raise ValueError(f"Rule references unknown canonical stage: '{rule.stage}'")
                
            if rule.board_section and rule.board_section not in self.board_sections:
                raise ValueError(f"Rule references unknown board section: '{rule.board_section}'")
                
            if rule.status not in valid_statuses:
                raise ValueError(f"Invalid rule status: '{rule.status}'")
                
            if rule.ready_behavior not in valid_ready:
                raise ValueError(f"Invalid ready_behavior: '{rule.ready_behavior}'")
                
            if rule.status == "APPROVED" and not rule.source:
                raise ValueError(f"APPROVED rule for '{rule.stage}' missing provenance (source).")
                
            if rule.stage in seen_stages:
                # Duplicate rule check
                prev_rule = seen_stages[rule.stage]
                if prev_rule.status == "APPROVED" and rule.status == "APPROVED":
                    if prev_rule.board_section != rule.board_section or prev_rule.ready_behavior != rule.ready_behavior:
                        raise ValueError(f"Conflicting APPROVED rules found for stage: '{rule.stage}'")
            
            seen_stages[rule.stage] = rule

    def get_stage_status_report(self) -> Dict[str, Any]:
        """
        Returns a summary of how all canonical stages are handled by the rules.
        """
        report = {
            "APPROVED": [],
            "UNRESOLVED": [],
            "AMBIGUOUS": [],
            "DISABLED": []
        }
        
        # Build map of stage to its defined rule (if any)
        rule_map = {r.stage: r for r in self.config.rules}
        
        for stage in self.canonical_stages:
            if stage in rule_map:
                r = rule_map[stage]
                report[r.status].append(r)
            else:
                # If no rule exists at all, it's UNRESOLVED
                report["UNRESOLVED"].append(
                    BusinessRule(stage=stage, status="UNRESOLVED")
                )
                
        return report
