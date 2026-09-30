import pytest
from pathlib import Path
import json
from court_board.validation.business_rule_validator import BusinessRuleValidator

@pytest.fixture
def base_config(tmp_path):
    stages_path = tmp_path / "stages.json"
    board_path = tmp_path / "board.json"
    
    with open(stages_path, "w") as f:
        json.dump([
            {"canonical_name": "StageA", "order": 1},
            {"canonical_name": "StageB", "order": 2},
            {"canonical_name": "StageC", "order": 3},
            {"canonical_name": "StageD", "order": 4}
        ], f)
        
    with open(board_path, "w") as f:
        json.dump({
            "sections": [
                {"id": "sec1", "name": "Section1", "order": 1, "ready_unready_behavior": "Ready", "stages": []},
                {"id": "sec2", "name": "OtherSection", "order": 2, "ready_unready_behavior": "Ready", "stages": []}
            ]
        }, f)
        
    return {"stages_path": str(stages_path), "board_path": str(board_path), "tmp_path": tmp_path}

def test_approved_officer_rule_loads(base_config):
    rules_path = base_config["tmp_path"] / "rules.json"
    with open(rules_path, "w") as f:
        json.dump({
            "rules": [
                {
                    "stage": "StageA",
                    "board_section": "Section1",
                    "status": "APPROVED",
                    "ready_behavior": "READY",
                    "source": "OFFICER_PROVIDED",
                    "source_note": "Rule A"
                }
            ]
        }, f)
        
    validator = BusinessRuleValidator(str(rules_path), base_config["stages_path"], base_config["board_path"])
    validator.validate()
    report = validator.get_stage_status_report()
    
    assert len(report["APPROVED"]) == 1
    assert report["APPROVED"][0].stage == "StageA"

def test_unknown_stage_rejected(base_config):
    rules_path = base_config["tmp_path"] / "rules.json"
    with open(rules_path, "w") as f:
        json.dump({
            "rules": [
                {
                    "stage": "UnknownStage",
                    "status": "UNRESOLVED"
                }
            ]
        }, f)
        
    validator = BusinessRuleValidator(str(rules_path), base_config["stages_path"], base_config["board_path"])
    with pytest.raises(ValueError, match="unknown canonical stage: 'UnknownStage'"):
        validator.validate()

def test_unknown_board_section_rejected(base_config):
    rules_path = base_config["tmp_path"] / "rules.json"
    with open(rules_path, "w") as f:
        json.dump({
            "rules": [
                {
                    "stage": "StageA",
                    "board_section": "UnknownSection",
                    "status": "APPROVED",
                    "source": "TEST"
                }
            ]
        }, f)
        
    validator = BusinessRuleValidator(str(rules_path), base_config["stages_path"], base_config["board_path"])
    with pytest.raises(ValueError, match="unknown board section: 'UnknownSection'"):
        validator.validate()

def test_conflicting_rules_detected(base_config):
    rules_path = base_config["tmp_path"] / "rules.json"
    with open(rules_path, "w") as f:
        json.dump({
            "rules": [
                {
                    "stage": "StageA", "board_section": "Section1", "status": "APPROVED", "source": "T1"
                },
                {
                    "stage": "StageA", "board_section": "OtherSection", "status": "APPROVED", "source": "T2"
                }
            ]
        }, f)
        
    validator = BusinessRuleValidator(str(rules_path), base_config["stages_path"], base_config["board_path"])
    with pytest.raises(ValueError, match="Conflicting APPROVED rules found for stage: 'StageA'"):
        validator.validate()

def test_unresolved_and_disabled_allowed(base_config):
    rules_path = base_config["tmp_path"] / "rules.json"
    with open(rules_path, "w") as f:
        json.dump({
            "rules": [
                {"stage": "StageA", "status": "UNRESOLVED"},
                {"stage": "StageB", "status": "DISABLED"}
            ]
        }, f)
        
    validator = BusinessRuleValidator(str(rules_path), base_config["stages_path"], base_config["board_path"])
    validator.validate()
    report = validator.get_stage_status_report()
    
    assert len(report["UNRESOLVED"]) == 3 # StageA explicit + StageC implicit + StageD implicit
    assert len(report["DISABLED"]) == 1

def test_missing_provenance_rejected(base_config):
    rules_path = base_config["tmp_path"] / "rules.json"
    with open(rules_path, "w") as f:
        json.dump({
            "rules": [
                {
                    "stage": "StageA",
                    "board_section": "Section1",
                    "status": "APPROVED"
                    # missing source
                }
            ]
        }, f)
        
    validator = BusinessRuleValidator(str(rules_path), base_config["stages_path"], base_config["board_path"])
    with pytest.raises(ValueError, match="missing provenance"):
        validator.validate()

def test_invalid_ready_behavior_rejected(base_config):
    rules_path = base_config["tmp_path"] / "rules.json"
    with open(rules_path, "w") as f:
        json.dump({
            "rules": [
                {
                    "stage": "StageA",
                    "board_section": "Section1",
                    "status": "APPROVED",
                    "ready_behavior": "INVALID_READY",
                    "source": "T1"
                }
            ]
        }, f)
        
    validator = BusinessRuleValidator(str(rules_path), base_config["stages_path"], base_config["board_path"])
    with pytest.raises(ValueError, match="Invalid ready_behavior"):
        validator.validate()

def test_all_canonical_stages_accounted_for():
    # Uses the real project configuration
    validator = BusinessRuleValidator()
    validator.validate()
    report = validator.get_stage_status_report()
    
    # Check that all 49 stages are somewhere in the report
    total_stages = len(report["APPROVED"]) + len(report["UNRESOLVED"]) + len(report["AMBIGUOUS"]) + len(report["DISABLED"])
    assert total_stages == len(validator.canonical_stages)
