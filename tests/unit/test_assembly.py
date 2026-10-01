import pytest
from court_board.domain.routing import BoardRoutingResult, BoardDestination
from court_board.domain.models import CaseRecord
from court_board.domain.board_template import BoardTemplate, BoardSection, BoardRow
from court_board.assembly.assembler import FinalBoardAssembler
from court_board.assembly.validator import FinalBoardValidator

@pytest.fixture
def sample_template():
    return BoardTemplate(sections=[
        BoardSection(id="hearing", name="Hearing", order=1, ready_unready_behavior="READY", rows=[
            BoardRow(id="h1", display_label="Evidence", canonical_stage_reference="Evidence", order=1)
        ]),
        BoardSection(id="part_heard", name="Part Heard", order=2, ready_unready_behavior="READY", rows=[]),
        BoardSection(id="313", name="313.0", order=3, ready_unready_behavior="READY", rows=[]),
        BoardSection(id="argument", name="Argument", order=4, ready_unready_behavior="READY", rows=[]),
        BoardSection(id="judgement", name="Judgement", order=5, ready_unready_behavior="READY", rows=[]),
        BoardSection(id="ma", name="M.A.", order=6, ready_unready_behavior="UNREADY", rows=[]),
        BoardSection(id="dv", name="D.V.", order=7, ready_unready_behavior="UNREADY", rows=[]),
        BoardSection(id="rcc", name="R.C.C.", order=8, ready_unready_behavior="UNREADY", rows=[
            BoardRow(id="rcc1", display_label="Dismissal Order", canonical_stage_reference="Dismissal Order", order=1)
        ]),
        BoardSection(id="scc", name="S.C.C.", order=9, ready_unready_behavior="UNREADY", rows=[
            BoardRow(id="scc1", display_label="Dismissal Order", canonical_stage_reference="Dismissal Order", order=1)
        ]),
        BoardSection(id="nbw", name="N.B.W. / B.W.", order=10, ready_unready_behavior="UNREADY", rows=[
            BoardRow(id="nbw1", display_label="N.B.W._Unready", canonical_stage_reference="N.B.W._Unready", order=1),
            BoardRow(id="nbw2", display_label="B.W._Unready", canonical_stage_reference="B.W._Unready", order=2)
        ])
    ])

def create_case(cases: str, purpose: str, ready: str, row: int):
    return CaseRecord(
        source_row_index=row,
        cases=cases,
        party_name="State vs X",
        date_of_registration="01-01-2020",
        age="5y",
        ready_unready_stayed=ready,
        next_date="",
        next_purpose=purpose,
        on_same_stage_since="",
        dormant_case_sine_die="",
        nature="",
        delay_reason=""
    )

def test_basic_assembly(sample_template):
    assembler = FinalBoardAssembler(sample_template)
    
    c1 = create_case("R.C.C./1/2026", "N.B.W._Unready", "Unready", 1)
    
    r1 = BoardRoutingResult(
        source_case=c1,
        source_row_index=1,
        canonical_stage="N.B.W._Unready",
        readiness_status="Unready",
        case_prefix="R.C.C.",
        routing_status="ROUTED",
        routing_reason="Rule",
        destinations=[
            BoardDestination(section_id="rcc", section_name="R.C.C.", row_id=None, row_name=None, source_stage="N.B.W._Unready", routing_reason="test"),
            BoardDestination(section_id="scc", section_name="S.C.C.", row_id=None, row_name=None, source_stage="N.B.W._Unready", routing_reason="test"),
            BoardDestination(section_id="nbw", section_name="N.B.W. / B.W.", row_id="nbw1", row_name="N.B.W._Unready", source_stage="N.B.W._Unready", routing_reason="test")
        ]
    )
    
    board = assembler.assemble([r1], "2026-07-01")
    
    assert len(board.sections) == 10
    
    # Verify exact sections order
    names = [s.section_name for s in board.sections]
    assert names == ["Hearing", "Part Heard", "313.0", "Argument", "Judgement", "M.A.", "D.V.", "R.C.C.", "S.C.C.", "N.B.W. / B.W."]
    
    # Verify entries count (3 destinations = 3 entries)
    total_entries = sum(len(s.entries) for s in board.sections)
    assert total_entries == 3
    
    rcc_sec = next(s for s in board.sections if s.section_id == "rcc")
    scc_sec = next(s for s in board.sections if s.section_id == "scc")
    nbw_sec = next(s for s in board.sections if s.section_id == "nbw")
    
    assert len(rcc_sec.entries) == 1
    assert len(scc_sec.entries) == 1
    assert len(nbw_sec.entries) == 1
    
    # Traceability
    assert rcc_sec.entries[0].source_row_number == 1
    assert rcc_sec.entries[0].optional_row_id is None
    
    validator = FinalBoardValidator(sample_template)
    validator.validate(board, [r1])

def test_source_row_ordering(sample_template):
    assembler = FinalBoardAssembler(sample_template)
    
    c1 = create_case("R.C.C./1/2026", "Awaiting Warrant", "Unready", 10)
    c2 = create_case("R.C.C./2/2026", "Awaiting Warrant", "Unready", 5)
    
    r1 = BoardRoutingResult(
        source_case=c1,
        source_row_index=10,
        canonical_stage="Awaiting Warrant",
        readiness_status="Unready",
        case_prefix="R.C.C.",
        routing_status="ROUTED",
        routing_reason="",
        destinations=[BoardDestination(section_id="rcc", section_name="R.C.C.", row_id=None, row_name=None, source_stage="Awaiting Warrant", routing_reason="test")]
    )
    r2 = BoardRoutingResult(
        source_case=c2,
        source_row_index=5,
        canonical_stage="Awaiting Warrant",
        readiness_status="Unready",
        case_prefix="R.C.C.",
        routing_status="ROUTED",
        routing_reason="",
        destinations=[BoardDestination(section_id="rcc", section_name="R.C.C.", row_id=None, row_name=None, source_stage="Awaiting Warrant", routing_reason="test")]
    )
    
    # Input them out of order
    board = assembler.assemble([r1, r2])
    
    rcc_sec = next(s for s in board.sections if s.section_id == "rcc")
    assert len(rcc_sec.entries) == 2
    
    # They should be sorted by source_row_index ascending
    assert rcc_sec.entries[0].source_row_number == 5
    assert rcc_sec.entries[1].source_row_number == 10

def test_no_unexpected_entries(sample_template):
    assembler = FinalBoardAssembler(sample_template)
    
    c1 = create_case("R.C.C./1/2026", "N.B.W._Unready", "Unready", 1)
    
    r1 = BoardRoutingResult(
        source_case=c1,
        source_row_index=1,
        canonical_stage="N.B.W._Unready",
        readiness_status="Unready",
        case_prefix="R.C.C.",
        routing_status="UNRESOLVED_ROUTING",
        routing_reason="Rule",
        destinations=[]
    )
    
    board = assembler.assemble([r1])
    total_entries = sum(len(s.entries) for s in board.sections)
    assert total_entries == 0

    validator = FinalBoardValidator(sample_template)
    validator.validate(board, [r1])
