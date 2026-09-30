import pytest
import os
import hashlib
from pathlib import Path
from court_board.io.importer import CourtBoardImporter
from court_board.classification.engine import StageClassificationEngine
from court_board.classification.collection import StageCollection
from court_board.rendering.stagewise_ods import StageWiseRenderer
from court_board.domain.models import CaseRecord

SAMPLE_FILE = "samples/01.07.2026.xlsx"

def get_file_hash(filepath: str) -> str:
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

@pytest.fixture
def engine():
    return StageClassificationEngine()

@pytest.fixture
def sample_records():
    if not os.path.exists(SAMPLE_FILE):
        pytest.skip(f"Sample file {SAMPLE_FILE} not found")
    importer = CourtBoardImporter(SAMPLE_FILE)
    records, validations = importer.load()
    return records

def test_whitespace_normalization(engine):
    # Mock a CaseRecord
    record1 = CaseRecord(
        source_row_index=1,
        cases="Case1",
        next_purpose="  Evidence  ",
    )
    result1 = engine.classify(record1)
    assert result1.normalized_next_purpose == "Evidence"
    assert result1.canonical_stage == "Evidence"
    assert result1.classification_status == "CLASSIFIED"

def test_semantically_different_stages_remain_different(engine):
    record1 = CaseRecord(source_row_index=1, cases="Case1", next_purpose="Arguments")
    record2 = CaseRecord(source_row_index=2, cases="Case2", next_purpose="Argument on Exh.____Ready")
    
    res1 = engine.classify(record1)
    res2 = engine.classify(record2)
    
    assert res1.normalized_next_purpose != res2.normalized_next_purpose
    assert res1.canonical_stage == "Arguments"
    assert res2.canonical_stage == "Argument on Exh.____Ready"

def test_unknown_next_purpose_unmapped(engine):
    record = CaseRecord(source_row_index=1, cases="Case1", next_purpose="Some New Stage That Does Not Exist")
    result = engine.classify(record)
    
    assert result.classification_status == "UNMAPPED"
    assert result.canonical_stage is None

def test_classification_invariants(engine, sample_records):
    collection = StageCollection(engine.get_stages())
    for record in sample_records:
        collection.add_result(engine.classify(record))
        
    # No case disappears / accountability
    assert collection.classified_count + collection.unmapped_count == len(sample_records)
    collection.verify_invariants(len(sample_records), 0)

    # Empty stages should still be present in get_all_stages()
    all_stages = collection.get_all_stages()
    assert len(all_stages) == len(engine.get_stages())

    # Check that known values classify correctly
    evidence_cases = collection.get_cases_for_stage("Evidence")
    assert len(evidence_cases) == 4
    
    nbw_ready_cases = collection.get_cases_for_stage("N.B.W._Ready")
    assert len(nbw_ready_cases) == 8

def test_stagewise_ods_generation(engine, sample_records, tmp_path):
    collection = StageCollection(engine.get_stages())
    for record in sample_records:
        collection.add_result(engine.classify(record))
        
    original_hash = get_file_hash(SAMPLE_FILE)
    
    output_ods = tmp_path / "01.07.2026_stagewise.ods"
    renderer = StageWiseRenderer(collection)
    renderer.render(str(output_ods))
    
    assert output_ods.exists()
    
    # Source remains unchanged
    new_hash = get_file_hash(SAMPLE_FILE)
    assert original_hash == new_hash

    # Read back the generated ODS to verify stage headings are present
    import pandas as pd
    df = pd.read_excel(str(output_ods), engine='odf', header=None)
    
    # Check that all canonical stage headings exist, even if empty
    content = df.fillna("").astype(str).values.flatten().tolist()
    
    for stage in engine.get_stages():
        heading = f"=== STAGE: {stage.canonical_name} ==="
        assert any(heading in cell for cell in content), f"Missing heading: {heading}"
