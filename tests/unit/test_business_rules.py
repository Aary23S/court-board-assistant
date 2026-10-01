import pytest
from pathlib import Path
import json
from court_board.validation.business_rule_validator import BusinessRuleValidator

@pytest.fixture
def base_config(tmp_path):
    template_path = tmp_path / "final_board_template.json"
    
    with open(template_path, "w") as f:
        json.dump({
            "sections": [
                {"id": "sec1", "name": "Section1", "order": 1, "ready_unready_behavior": "READY", "rows": []},
                {"id": "sec2", "name": "OtherSection", "order": 2, "ready_unready_behavior": "READY", "rows": []}
            ]
        }, f)
        
    return {"template_path": str(template_path), "tmp_path": tmp_path}

def test_approved_officer_rule_loads(base_config):
    rules_path = base_config["tmp_path"] / "rules.json"
    with open(rules_path, "w") as f:
        json.dump({
            "rules": [
                {
                    "condition": "Ready",
                    "destinations": ["Section1"],
                    "status": "APPROVED",
                    "source": "OFFICER_PROVIDED",
                    "source_note": "Rule A"
                }
            ]
        }, f)
        
    validator = BusinessRuleValidator(str(rules_path), base_config["template_path"])
    validator.validate()
    assert len(validator.config.rules) == 1

def test_unknown_board_section_rejected(base_config):
    rules_path = base_config["tmp_path"] / "rules.json"
    with open(rules_path, "w") as f:
        json.dump({
            "rules": [
                {
                    "condition": "Ready",
                    "destinations": ["UnknownSection"],
                    "status": "APPROVED",
                    "source": "TEST"
                }
            ]
        }, f)
        
    validator = BusinessRuleValidator(str(rules_path), base_config["template_path"])
    with pytest.raises(ValueError, match="unknown board section: 'UnknownSection'"):
        validator.validate()

def test_duplicate_condition_rejected(base_config):
    rules_path = base_config["tmp_path"] / "rules.json"
    with open(rules_path, "w") as f:
        json.dump({
            "rules": [
                {
                    "condition": "Ready", "destinations": ["Section1"], "status": "APPROVED", "source": "T1"
                },
                {
                    "condition": "Ready", "destinations": ["OtherSection"], "status": "APPROVED", "source": "T2"
                }
            ]
        }, f)
        
    validator = BusinessRuleValidator(str(rules_path), base_config["template_path"])
    with pytest.raises(ValueError, match="Duplicate condition in rules: 'Ready'"):
        validator.validate()

def test_missing_provenance_rejected(base_config):
    rules_path = base_config["tmp_path"] / "rules.json"
    with open(rules_path, "w") as f:
        json.dump({
            "rules": [
                {
                    "condition": "Ready",
                    "destinations": ["Section1"],
                    "status": "APPROVED"
                    # missing source
                }
            ]
        }, f)
        
    validator = BusinessRuleValidator(str(rules_path), base_config["template_path"])
    with pytest.raises(ValueError, match="missing provenance"):
        validator.validate()

def test_real_rules_validate():
    # Uses the real project configuration
    validator = BusinessRuleValidator()
    validator.validate()
    assert len(validator.config.rules) == 10
