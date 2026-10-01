import pytest
import json
import hashlib
from pathlib import Path

from court_board.routing.engine import RoutingEngine
from court_board.classification.engine import StageClassificationEngine
from court_board.io.importer import CourtBoardImporter
from court_board.assembly.assembler import FinalBoardAssembler
from court_board.rendering.final_board_ods import FinalBoardODSRenderer
from court_board.domain.models import CaseRecord
from odf.opendocument import load
from odf.table import Table, TableRow

@pytest.fixture
def real_sample_path():
    return Path("samples/01.07.2026.xlsx")

@pytest.fixture
def routing_engine():
    return RoutingEngine()

@pytest.fixture
def stage_classifier():
    return StageClassificationEngine()

def test_1_and_2_evidence_part_heard_routes_to_part_heard(routing_engine, stage_classifier):
    case = CaseRecord(
        source_row_index=1,
        cases="S.C.C./301071/2012",
        next_purpose="Evidence Part Heard",
        ready_unready_stayed="Ready"
    )
    class_res = stage_classifier.classify(case)
    canonical_stage = class_res.canonical_stage
    assert canonical_stage == "Evidence Part Heard"
    
    result = routing_engine.route(case, canonical_stage)
    assert result.routing_status == "ROUTED"
    assert len(result.destinations) == 1
    assert result.destinations[0].section_name == "Part Heard"
    assert result.destinations[0].section_name != "Hearing"

def test_3_rcc_nbw_unready(routing_engine):
    # TEST 3: R.C.C. + N.B.W._Unready -> R.C.C., S.C.C., N.B.W. / B.W.
    case = CaseRecord(
        source_row_index=1,
        cases="R.C.C./300258/1996",
        next_purpose="N.B.W._Unready",
        ready_unready_stayed="Unready"
    )
    result = routing_engine.route(case, "N.B.W._Unready")
    assert result.routing_status == "ROUTED"
    sections = {d.section_name for d in result.destinations}
    assert sections == {"R.C.C.", "S.C.C.", "N.B.W. / B.W."}

def test_4_scc_nbw_unready(routing_engine):
    # TEST 4: S.C.C. + N.B.W._Unready -> R.C.C., S.C.C., N.B.W. / B.W.
    case = CaseRecord(
        source_row_index=1,
        cases="S.C.C./100/2020",
        next_purpose="N.B.W._Unready",
        ready_unready_stayed="Unready"
    )
    result = routing_engine.route(case, "N.B.W._Unready")
    assert result.routing_status == "ROUTED"
    sections = {d.section_name for d in result.destinations}
    assert sections == {"R.C.C.", "S.C.C.", "N.B.W. / B.W."}

def test_5_rcc_normal_unready(routing_engine):
    # TEST 5: R.C.C. + normal Unready stage -> R.C.C., S.C.C.
    case = CaseRecord(
        source_row_index=1,
        cases="R.C.C./100/2020",
        next_purpose="Dismissal Order",
        ready_unready_stayed="Unready"
    )
    result = routing_engine.route(case, "Dismissal Order")
    assert result.routing_status == "ROUTED"
    sections = {d.section_name for d in result.destinations}
    assert sections == {"R.C.C.", "S.C.C."}

def test_6_scc_normal_unready(routing_engine):
    # TEST 6: S.C.C. + normal Unready stage -> R.C.C., S.C.C.
    case = CaseRecord(
        source_row_index=1,
        cases="S.C.C./100/2020",
        next_purpose="Dismissal Order",
        ready_unready_stayed="Unready"
    )
    result = routing_engine.route(case, "Dismissal Order")
    assert result.routing_status == "ROUTED"
    sections = {d.section_name for d in result.destinations}
    assert sections == {"R.C.C.", "S.C.C."}

def test_7_8_9_10_renderer_sections_and_merged_structure(tmp_path, routing_engine):
    # TEST 7-10: Final renderer physical structure, sections, RCC/SCC merged structure, NBW/BW section
    importer = CourtBoardImporter("samples/01.07.2026.xlsx")
    classifier = StageClassificationEngine()
    cases, _ = importer.load()
    
    routing_results = []
    for c in cases:
        canonical = classifier.classify(c).canonical_stage
        res = routing_engine.route(c, canonical)
        routing_results.append(res)
        
    assembler = FinalBoardAssembler(routing_engine.template)
    board = assembler.assemble(routing_results, board_date="01.07.2026")
    
    out_file = tmp_path / "test_board.ods"
    renderer = FinalBoardODSRenderer(board)
    renderer.render(str(out_file))
    
    assert out_file.exists()
    
    doc = load(str(out_file))
    table = doc.spreadsheet.getElementsByType(Table)[0]
    rows = table.getElementsByType(TableRow)
    header_row = rows[4]  # Row 5 (0-indexed 4)
    cells = header_row.childNodes
    
    headers_found = []
    for c in cells:
        text = str(c)
        if text.strip():
            headers_found.append(text.strip())
            
    expected_sections = [
        "Hearing", "Part Heard", "313", "Argument", "Judgement",
        "M.A.", "D.V.", "R.C.C.", "S.C.C.", "N.B.W. / B.W."
    ]
    for sec in expected_sections:
        assert any(sec in h for h in headers_found), f"Missing section: {sec}"
        
    # Check RCC and SCC spans
    rcc_cell = next(c for c in cells if "R.C.C." in str(c))
    assert rcc_cell.getAttribute("numbercolumnsspanned") == "2"
    
    scc_cell = next(c for c in cells if "S.C.C." in str(c))
    assert scc_cell.getAttribute("numbercolumnsspanned") == "2"

def test_11_93_destinations_result_in_93_final_board_entries(routing_engine):
    # TEST 11: 93 routing destinations result in 93 final-board entries for real sample
    importer = CourtBoardImporter("samples/01.07.2026.xlsx")
    classifier = StageClassificationEngine()
    cases, _ = importer.load()
    
    routing_results = []
    for c in cases:
        canonical = classifier.classify(c).canonical_stage
        res = routing_engine.route(c, canonical)
        routing_results.append(res)
        
    total_destinations = sum(len(r.destinations) for r in routing_results if r.routing_status == "ROUTED")
    assert total_destinations == 93
    
    assembler = FinalBoardAssembler(routing_engine.template)
    board = assembler.assemble(routing_results, board_date="01.07.2026")
    
    total_entries = sum(len(sec.entries) for sec in board.sections)
    assert total_entries == 93

def test_12_source_file_remains_unchanged(real_sample_path):
    # TEST 12: Source file hash before and after processing remains identical
    with open(real_sample_path, "rb") as f:
        hash_before = hashlib.sha256(f.read()).hexdigest()
        
    importer = CourtBoardImporter(str(real_sample_path))
    _ = importer.load()
    
    with open(real_sample_path, "rb") as f:
        hash_after = hashlib.sha256(f.read()).hexdigest()
        
    assert hash_before == hash_after
