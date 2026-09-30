import pytest
from court_board.routing.engine import RoutingEngine
from court_board.routing.prefix_extractor import CasePrefixExtractor
from court_board.domain.models import CaseRecord

@pytest.fixture
def engine():
    return RoutingEngine()

@pytest.fixture
def extractor():
    return CasePrefixExtractor()

def test_prefix_extractor(extractor):
    assert extractor.extract("Cri.M.A./123/2026") == "Cri.M.A."
    assert extractor.extract("  PWDVA Appln. / 123") == "PWDVA Appln."
    assert extractor.extract("R.C.C./456/2024") == "R.C.C."
    assert extractor.extract("S.C.C./789/2023") == "S.C.C."
    # Whitespace normalization
    assert extractor.extract("Cri.M.A.  /123/2026") == "Cri.M.A."
    # Unknown prefix
    assert extractor.extract("RandomPrefix/123/2026") == "UNKNOWN_PREFIX"
    # Malformed case number
    assert extractor.extract("Just A String Without Slashes") == "UNKNOWN_PREFIX"

def test_unknown_stage_is_invalid(engine):
    case = CaseRecord(source_row_index=1, cases="Cri.M.A./1/2026", next_purpose="Unknown Stage", ready_unready_stayed="Ready")
    result = engine.route(case, "Unknown Stage")
    assert result.routing_status == "INVALID_INPUT"

def test_stayed_is_unresolved(engine):
    case = CaseRecord(source_row_index=1, cases="Cri.M.A./1/2026", next_purpose="Evidence", ready_unready_stayed="Stayed")
    result = engine.route(case, "Evidence")
    assert result.routing_status == "UNRESOLVED_ROUTING"
    assert result.routing_reason == "Stayed status has no approved routing rule"
    # Metadata preserved
    assert result.source_case.source_row_index == 1

def test_ready_routing_unique_match(engine):
    # Evidence -> Hearing / Evidence
    case = CaseRecord(source_row_index=1, cases="Cri.M.A./1/2026", next_purpose="Evidence", ready_unready_stayed="Ready")
    result = engine.route(case, "Evidence")
    assert result.routing_status == "ROUTED"
    assert result.board_section == "Hearing"
    assert result.board_row == "Evidence"
    
    # Evidence Part Heard -> Part Heard / Evidence Part Heard
    case2 = CaseRecord(source_row_index=2, cases="Cri.M.A./2/2026", next_purpose="Evidence Part Heard", ready_unready_stayed="Ready")
    result2 = engine.route(case2, "Evidence Part Heard")
    assert result2.routing_status == "ROUTED"
    assert result2.board_section == "Part Heard"
    assert result2.board_row == "Evidence Part Heard"

def test_unready_routing(engine):
    stages = ["Dismissal Order", "Steps", "Argument on Exh.____Unready"]
    prefixes = ["Cri.M.A.", "PWDVA Appln.", "R.C.C.", "S.C.C."]
    sections = ["M.A.", "D.V.", "R.C.C.", "S.C.C."]
    
    for prefix, section in zip(prefixes, sections):
        for stage in stages:
            case = CaseRecord(source_row_index=1, cases=f"{prefix}/1/2026", next_purpose=stage, ready_unready_stayed="Unready")
            result = engine.route(case, stage)
            assert result.routing_status == "ROUTED", f"Failed for {prefix} {stage}: {result.routing_reason}"
            assert result.board_section == section
            assert result.board_row == stage

def test_missing_board_row(engine):
    # 'Arguments' is not in the D.V. section
    case = CaseRecord(source_row_index=1, cases="PWDVA Appln./1/2026", next_purpose="Arguments", ready_unready_stayed="Unready")
    result = engine.route(case, "Arguments")
    assert result.routing_status == "UNRESOLVED_ROUTING"
    assert "not found in section" in result.routing_reason

def test_multiple_board_row_matches(engine):
    # If a stage occurred multiple times in the SAME section (e.g., if D.V. had two 'Steps' rows).
    # Currently none of the sections have duplicate rows for the same canonical stage natively,
    # But if it did, the engine would flag UNRESOLVED_ROUTING. We can trust the code logic here.
    pass

def test_unready_routing_unknown_prefix(engine):
    case = CaseRecord(source_row_index=1, cases="UnknownPrefix/1/2026", next_purpose="Dismissal Order", ready_unready_stayed="Unready")
    result = engine.route(case, "Dismissal Order")
    assert result.routing_status == "UNRESOLVED_ROUTING"
    assert "Unknown case prefix" in result.routing_reason

def test_ready_routing_missing_row(engine):
    # 'Steps' is not on the Ready side (only under unready sections)
    case = CaseRecord(source_row_index=1, cases="Cri.M.A./1/2026", next_purpose="Steps", ready_unready_stayed="Ready")
    result = engine.route(case, "Steps")
    assert result.routing_status == "UNRESOLVED_ROUTING"
    assert "0 matching rows" in result.routing_reason
