import pytest
from pathlib import Path
import json
from court_board.validation.board_validator import BoardValidator, BoardSectionConfig, BoardLayoutConfig

def test_board_configuration_loads_successfully():
    validator = BoardValidator()
    assert validator.layout is not None
    assert len(validator.layout.sections) > 0

def test_all_referenced_stages_exist():
    validator = BoardValidator()
    # Will not raise if everything is correct
    validator.validate_structure()

def test_nonexistent_stage_references_detected(tmp_path):
    # Mock invalid layout
    layout_path = tmp_path / "bad_layout.json"
    bad_layout = {
        "sections": [
            {
                "id": "s1", "name": "Section 1", "order": 1, 
                "ready_unready_behavior": "Ready",
                "stages": ["NonExistent Stage"]
            }
        ]
    }
    with open(layout_path, "w") as f:
        json.dump(bad_layout, f)
        
    validator = BoardValidator(board_config_path=str(layout_path))
    with pytest.raises(ValueError, match="references non-existent canonical stage"):
        validator.validate_structure()

def test_duplicate_section_ids_detected(tmp_path):
    layout_path = tmp_path / "bad_layout.json"
    bad_layout = {
        "sections": [
            {"id": "dup", "name": "S1", "order": 1, "ready_unready_behavior": "Ready", "stages": []},
            {"id": "dup", "name": "S2", "order": 2, "ready_unready_behavior": "Ready", "stages": []}
        ]
    }
    with open(layout_path, "w") as f:
        json.dump(bad_layout, f)
        
    validator = BoardValidator(board_config_path=str(layout_path))
    with pytest.raises(ValueError, match="Duplicate section ID: dup"):
        validator.validate_structure()

def test_mappings_determine_correct_status(tmp_path):
    stages_path = tmp_path / "stages.json"
    layout_path = tmp_path / "layout.json"
    
    stages = [
        {"canonical_name": "StageA", "order": 1},
        {"canonical_name": "StageB", "order": 2},
        {"canonical_name": "StageC", "order": 3}
    ]
    with open(stages_path, "w") as f:
        json.dump(stages, f)
        
    layout = {
        "sections": [
            {"id": "s1", "name": "S1", "order": 1, "ready_unready_behavior": "Ready", "stages": ["StageA"]},
            {"id": "s2", "name": "S2", "order": 2, "ready_unready_behavior": "Ready", "stages": ["StageA"]}, # Ambiguous
            {"id": "s3", "name": "S3", "order": 3, "ready_unready_behavior": "Ready", "stages": ["StageB"]}
        ]
    }
    with open(layout_path, "w") as f:
        json.dump(layout, f)
        
    validator = BoardValidator(stages_config_path=str(stages_path), board_config_path=str(layout_path))
    mappings = validator.determine_stage_mappings()
    
    assert mappings["StageA"]["status"] == "AMBIGUOUS"
    assert mappings["StageB"]["status"] == "UNIQUE"
    assert mappings["StageC"]["status"] == "UNRESOLVED"
