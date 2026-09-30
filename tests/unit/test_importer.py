import pytest
import os
import hashlib
from pathlib import Path
from court_board.io.importer import CourtBoardImporter

SAMPLE_FILE = "samples/01.07.2026.xlsx"

def get_file_hash(filepath: str) -> str:
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def test_importer_preserves_source_hash():
    """Verify that the source file is completely unmodified after import."""
    if not os.path.exists(SAMPLE_FILE):
        pytest.skip(f"Sample file {SAMPLE_FILE} not found")
        
    original_hash = get_file_hash(SAMPLE_FILE)
    
    importer = CourtBoardImporter(SAMPLE_FILE)
    records, validations = importer.load()
    
    new_hash = get_file_hash(SAMPLE_FILE)
    assert original_hash == new_hash, "Source file was modified during import!"

def test_importer_loads_cases():
    """Test successful import of the reference dataset."""
    if not os.path.exists(SAMPLE_FILE):
        pytest.skip(f"Sample file {SAMPLE_FILE} not found")
        
    importer = CourtBoardImporter(SAMPLE_FILE)
    records, validations = importer.load()
    
    # We found 68 rows in our exploration (total rows minus headers)
    # Some might be empty or warnings, but all 68 should be records.
    assert len(records) > 0, "No records were extracted"
    assert len(records) == 68, f"Expected 68 cases, got {len(records)}"

    # Check that required properties are extracted
    first_record = records[0]
    assert first_record.source_row_index is not None
    assert first_record.cases is not None
    assert first_record.next_purpose is not None

def test_importer_malformed_handling(tmp_path):
    """Test handling of missing columns."""
    import pandas as pd
    
    # Create a malformed excel file without "Next Purpose"
    malformed = tmp_path / "malformed.xlsx"
    df = pd.DataFrame({
        "Sr. No.": [1],
        "Cases": ["Case1"]
        # Missing Next Purpose
    })
    df.to_excel(malformed, index=False, header=True)
    
    importer = CourtBoardImporter(str(malformed))
    records, validations = importer.load()
    
    # Should flag missing column
    errors = [v for v in validations if v.status == "ERROR"]
    assert len(errors) > 0
    assert any("Next Purpose" in e.message for e in errors)
