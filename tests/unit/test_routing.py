import pytest
import json
from pathlib import Path
from court_board.routing.engine import RoutingEngine
from court_board.domain.models import CaseRecord

@pytest.fixture
def mock_engine(tmp_path):
    template_path = tmp_path / "mock_template.json"
    
    template = {
        "sections": [
            {
                "id": "hearing", "name": "Hearing", "order": 1, "ready_unready_behavior": "READY",
                "rows": [{"id": "h1", "display_label": "Hearing", "canonical_stage_reference": "Hearing", "order": 1}]
            },
            {
                "id": "ma", "name": "M.A.", "order": 2, "ready_unready_behavior": "UNREADY",
                "rows": [
                    {"id": "ma1", "display_label": "Dismissal Order", "canonical_stage_reference": "Dismissal Order", "order": 1}
                ]
            },
            {
                "id": "dv", "name": "D.V.", "order": 3, "ready_unready_behavior": "UNREADY",
                "rows": [
                    {"id": "dv1", "display_label": "Dismissal Order", "canonical_stage_reference": "Dismissal Order", "order": 1}
                ]
            },
            {
                "id": "rcc", "name": "R.C.C.", "order": 4, "ready_unready_behavior": "UNREADY",
                "rows": [
                    {"id": "rcc1", "display_label": "Dismissal Order", "canonical_stage_reference": "Dismissal Order", "order": 1}
                ]
            },
            {
                "id": "scc", "name": "S.C.C.", "order": 5, "ready_unready_behavior": "UNREADY",
                "rows": [
                    {"id": "scc1", "display_label": "Dismissal Order", "canonical_stage_reference": "Dismissal Order", "order": 1}
                ]
            },
            {
                "id": "nbw", "name": "N.B.W. / B.W.", "order": 6, "ready_unready_behavior": "UNREADY",
                "rows": [
                    {"id": "nbw1", "display_label": "N.B.W._Unready", "canonical_stage_reference": "N.B.W._Unready", "order": 1},
                    {"id": "nbw2", "display_label": "B.W._Unready", "canonical_stage_reference": "B.W._Unready", "order": 2}
                ]
            }
        ]
    }
    
    with open(template_path, "w") as f:
        json.dump(template, f)
        
    return RoutingEngine(template_path=str(template_path))

def test_ready_routing(mock_engine):
    stages = ["Evidence", "Steps", "Reply/Say"]
    for stage in stages:
        case = CaseRecord(source_row_index=1, cases="Cri.M.A./1/2026", next_purpose=stage, ready_unready_stayed="Ready")
        result = mock_engine.route(case, stage)
        assert result.routing_status == "ROUTED"
        assert len(result.destinations) == 1
        assert result.destinations[0].section_name == "Hearing"

def test_unready_routing_ma(mock_engine):
    case = CaseRecord(source_row_index=1, cases="Cri.M.A./1/2026", next_purpose="Dismissal Order", ready_unready_stayed="Unready")
    result = mock_engine.route(case, "Dismissal Order")
    assert result.routing_status == "ROUTED"
    assert len(result.destinations) == 1
    assert result.destinations[0].section_name == "M.A."
    
def test_unready_routing_dv(mock_engine):
    case = CaseRecord(source_row_index=1, cases="PWDVA Appln./1/2026", next_purpose="Dismissal Order", ready_unready_stayed="Unready")
    result = mock_engine.route(case, "Dismissal Order")
    assert result.routing_status == "ROUTED"
    assert len(result.destinations) == 1
    assert result.destinations[0].section_name == "D.V."

def test_unready_routing_rcc(mock_engine):
    case = CaseRecord(source_row_index=1, cases="R.C.C./1/2026", next_purpose="Dismissal Order", ready_unready_stayed="Unready")
    result = mock_engine.route(case, "Dismissal Order")
    assert result.routing_status == "ROUTED"
    assert len(result.destinations) == 2
    assert {d.section_name for d in result.destinations} == {"R.C.C.", "S.C.C."}

def test_unready_routing_scc(mock_engine):
    case = CaseRecord(source_row_index=1, cases="S.C.C./1/2026", next_purpose="Dismissal Order", ready_unready_stayed="Unready")
    result = mock_engine.route(case, "Dismissal Order")
    assert result.routing_status == "ROUTED"
    assert len(result.destinations) == 2
    assert {d.section_name for d in result.destinations} == {"R.C.C.", "S.C.C."}

def test_unready_routing_rcc_nbw(mock_engine):
    case = CaseRecord(source_row_index=1, cases="R.C.C./1/2026", next_purpose="N.B.W._Unready", ready_unready_stayed="Unready")
    result = mock_engine.route(case, "N.B.W._Unready")
    assert result.routing_status == "ROUTED"
    assert len(result.destinations) == 3
    assert {d.section_name for d in result.destinations} == {"R.C.C.", "S.C.C.", "N.B.W. / B.W."}

def test_unready_routing_ma_nbw(mock_engine):
    case = CaseRecord(source_row_index=1, cases="Cri.M.A./1/2026", next_purpose="N.B.W._Unready", ready_unready_stayed="Unready")
    result = mock_engine.route(case, "N.B.W._Unready")
    assert result.routing_status == "ROUTED"
    assert len(result.destinations) == 2
    assert {d.section_name for d in result.destinations} == {"M.A.", "N.B.W. / B.W."}

def test_unready_routing_dv_nbw(mock_engine):
    case = CaseRecord(source_row_index=1, cases="PWDVA Appln./1/2026", next_purpose="N.B.W._Unready", ready_unready_stayed="Unready")
    result = mock_engine.route(case, "N.B.W._Unready")
    assert result.routing_status == "ROUTED"
    assert len(result.destinations) == 2
    assert {d.section_name for d in result.destinations} == {"D.V.", "N.B.W. / B.W."}
    
def test_unready_routing_scc_nbw(mock_engine):
    case = CaseRecord(source_row_index=1, cases="S.C.C./1/2026", next_purpose="N.B.W._Unready", ready_unready_stayed="Unready")
    result = mock_engine.route(case, "N.B.W._Unready")
    assert result.routing_status == "ROUTED"
    assert len(result.destinations) == 3
    assert {d.section_name for d in result.destinations} == {"R.C.C.", "S.C.C.", "N.B.W. / B.W."}
    
    # Assert section-level placement works correctly: rcc and scc should have row_id=None
    rcc_dest = next(d for d in result.destinations if d.section_name == "R.C.C.")
    assert rcc_dest.row_id is None
    nbw_dest = next(d for d in result.destinations if d.section_name == "N.B.W. / B.W.")
    assert nbw_dest.row_id == "nbw1"

def test_unready_routing_rcc_bw(mock_engine):
    case = CaseRecord(source_row_index=1, cases="R.C.C./1/2026", next_purpose="B.W._Unready", ready_unready_stayed="Unready")
    result = mock_engine.route(case, "B.W._Unready")
    assert result.routing_status == "ROUTED"
    assert len(result.destinations) == 3
    assert {d.section_name for d in result.destinations} == {"R.C.C.", "S.C.C.", "N.B.W. / B.W."}

def test_unready_routing_scc_bw(mock_engine):
    case = CaseRecord(source_row_index=1, cases="S.C.C./1/2026", next_purpose="B.W._Unready", ready_unready_stayed="Unready")
    result = mock_engine.route(case, "B.W._Unready")
    assert result.routing_status == "ROUTED"
    assert len(result.destinations) == 3
    assert {d.section_name for d in result.destinations} == {"R.C.C.", "S.C.C.", "N.B.W. / B.W."}

def test_stayed_is_unresolved(mock_engine):
    case = CaseRecord(source_row_index=1, cases="Cri.M.A./1/2026", next_purpose="Evidence", ready_unready_stayed="Stayed")
    result = mock_engine.route(case, "Evidence")
    assert result.routing_status == "UNRESOLVED_ROUTING"
    assert len(result.destinations) == 0

def test_no_case_loss_invariant(mock_engine):
    cases = [
        CaseRecord(source_row_index=1, cases="Cri.M.A./1/2026", next_purpose="Dismissal Order", ready_unready_stayed="Unready"),
        CaseRecord(source_row_index=2, cases="R.C.C./2/2026", next_purpose="N.B.W._Unready", ready_unready_stayed="Unready"),
        CaseRecord(source_row_index=3, cases="S.C.C./3/2026", next_purpose="Evidence", ready_unready_stayed="Stayed")
    ]
    results = [mock_engine.route(c, c.next_purpose) for c in cases]
    assert len(results) == len(cases)
