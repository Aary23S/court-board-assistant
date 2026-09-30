import pytest
import json
from pathlib import Path
from court_board.validation.board_template_validator import BoardTemplateValidator

@pytest.fixture
def validator():
    # Use the real configurations
    return BoardTemplateValidator()

def test_template_contains_exactly_10_sections(validator):
    assert len(validator.template.sections) == 10

def test_template_hearing_section(validator):
    hearing = next(s for s in validator.template.sections if s.name == "Hearing")
    rows = [r.display_label for r in hearing.rows]
    assert "Evidence" in rows
    assert "N.B.W._Ready" in rows

def test_template_part_heard(validator):
    part_heard = next(s for s in validator.template.sections if s.name == "Part Heard")
    rows = [r.display_label for r in part_heard.rows]
    assert "Evidence Part Heard" in rows

def test_template_313(validator):
    s313 = next(s for s in validator.template.sections if s.name == "313")
    rows = [r.display_label for r in s313.rows]
    assert "Statement U/sec.313 Cr.P.C." in rows

def test_template_argument(validator):
    arg = next(s for s in validator.template.sections if s.name == "Argument")
    rows = [r.display_label for r in arg.rows]
    assert "Arguments" in rows

def test_template_judgement(validator):
    judge = next(s for s in validator.template.sections if s.name == "Judgement")
    rows = [r.display_label for r in judge.rows]
    assert "Judgement" in rows

def test_template_dismissal_order_in_multiple_sections(validator):
    for sec_name in ["Hearing", "M.A.", "D.V.", "R.C.C.", "S.C.C."]:
        sec = next(s for s in validator.template.sections if s.name == sec_name)
        rows = [r.display_label for r in sec.rows]
        assert "Dismissal Order" in rows

def test_template_steps_in_multiple_sections(validator):
    for sec_name in ["M.A.", "D.V.", "R.C.C.", "S.C.C."]:
        sec = next(s for s in validator.template.sections if s.name == sec_name)
        rows = [r.display_label for r in sec.rows]
        assert "Steps" in rows

def test_template_nbw_bw(validator):
    nbw = next(s for s in validator.template.sections if s.name == "N.B.W. / B.W.")
    rows = [r.display_label for r in nbw.rows]
    assert "N.B.W._Unready" in rows
    assert "B.W._Unready" in rows

def test_validator_detects_duplicate_section_ids(tmp_path):
    # Mock template
    template_path = tmp_path / "template.json"
    stages_path = tmp_path / "stages.json"
    
    with open(stages_path, "w") as f: json.dump([], f)
    
    bad_template = {
        "sections": [
            {"id": "s1", "name": "S1", "order": 1, "ready_unready_behavior": "READY", "rows": []},
            {"id": "s1", "name": "S2", "order": 2, "ready_unready_behavior": "READY", "rows": []}
        ]
    }
    with open(template_path, "w") as f: json.dump(bad_template, f)
    
    val = BoardTemplateValidator(str(template_path), str(stages_path))
    # It first checks length == 10, so let's make it 10
    bad_template["sections"] += [{"id": f"x{i}", "name": f"X{i}", "order": i+2, "ready_unready_behavior": "READY", "rows": []} for i in range(8)]
    with open(template_path, "w") as f: json.dump(bad_template, f)
    val = BoardTemplateValidator(str(template_path), str(stages_path))
    with pytest.raises(ValueError, match="Duplicate section ID: s1"):
        val.validate()
        
def test_validator_detects_unknown_canonical_reference(tmp_path):
    template_path = tmp_path / "template.json"
    stages_path = tmp_path / "stages.json"
    
    with open(stages_path, "w") as f: 
        json.dump([{"canonical_name": "ValidStage", "order": 1}], f)
        
    bad_template = {
        "sections": [
            {"id": f"s{i}", "name": f"S{i}", "order": i, "ready_unready_behavior": "READY", "rows": []}
            for i in range(10)
        ]
    }
    bad_template["sections"][0]["rows"].append(
        {"id": "r1", "display_label": "Unknown", "order": 1, "canonical_stage_reference": "UnknownStage"}
    )
    with open(template_path, "w") as f: json.dump(bad_template, f)
    
    val = BoardTemplateValidator(str(template_path), str(stages_path))
    with pytest.raises(ValueError, match="references unknown canonical stage 'UnknownStage'"):
        val.validate()
