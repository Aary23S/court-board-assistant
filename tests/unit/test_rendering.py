import pytest
import pandas as pd
from pathlib import Path

from court_board.domain.routing import BoardRoutingResult, BoardDestination
from court_board.domain.models import CaseRecord
from court_board.domain.board_assembly import FinalBoard, FinalBoardSection, FinalBoardEntry
from court_board.rendering.final_board_ods import FinalBoardODSRenderer

def test_final_board_round_trip(tmp_path):
    # 1. Build a dummy board
    dest1 = BoardDestination(section_id="rcc", section_name="R.C.C.", row_id=None, row_name=None, source_stage="Stage", routing_reason="")
    dest2 = BoardDestination(section_id="scc", section_name="S.C.C.", row_id=None, row_name=None, source_stage="Stage", routing_reason="")
    
    e1 = FinalBoardEntry(
        case_number="R.C.C./101/2026", party_name="A vs B", source_row_number=1,
        registration_date="", age="", readiness_status="Unready", next_date="",
        next_purpose="", canonical_stage="", on_same_stage_since="", dormant_status="",
        nature="", delay_reason="", routing_reason="", source_destination=dest1
    )
    e2 = FinalBoardEntry(
        case_number="R.C.C./101/2026", party_name="A vs B", source_row_number=1,
        registration_date="", age="", readiness_status="Unready", next_date="",
        next_purpose="", canonical_stage="", on_same_stage_since="", dormant_status="",
        nature="", delay_reason="", routing_reason="", source_destination=dest2
    )
    
    board = FinalBoard(date="08.05.2026", sections=[
        FinalBoardSection(section_id="rcc", section_name="R.C.C.", order=8, entries=[e1]),
        FinalBoardSection(section_id="scc", section_name="S.C.C.", order=9, entries=[e2])
    ])
    
    renderer = FinalBoardODSRenderer(board)
    out_path = tmp_path / "test_board.ods"
    
    # 2. Render
    renderer.render(str(out_path))
    
    assert out_path.exists()
    
    # 3. Reopen ODS using pandas
    df = pd.read_excel(str(out_path), engine='odf', header=None)
    
    # Check headers in row 4 (0-indexed)
    headers = df.iloc[4].fillna("").tolist()
    assert "R.C.C." in headers
    assert "S.C.C." in headers
    
    rcc_idx = headers.index("R.C.C.")
    scc_idx = headers.index("S.C.C.")
    
    # 4. Extract visible case identifiers from row 5 onwards
    rcc_cases = df.iloc[5:, rcc_idx].dropna().tolist()
    scc_cases = df.iloc[5:, scc_idx].dropna().tolist()
    
    # 5. Confirm expected
    assert "R.C.C./101/2026" in rcc_cases
    assert "R.C.C./101/2026" in scc_cases
