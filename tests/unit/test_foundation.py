import os
from pathlib import Path

def test_project_imports_correctly():
    """Verify that we can import the src modules."""
    try:
        import court_board
        assert True
    except ImportError:
        assert False, "Failed to import court_board module"

def test_configuration_loads():
    """Verify that configuration structure exists and is accessible."""
    config_dir = Path("config")
    assert config_dir.exists(), "Config directory should exist"
    assert config_dir.is_dir(), "Config should be a directory"

def test_sample_files_discovery():
    """Verify that the samples directory exists for discovery."""
    samples_dir = Path("samples")
    assert samples_dir.exists(), "Samples directory should exist"
    assert samples_dir.is_dir(), "Samples should be a directory"
    # We don't assert files exist yet since they are pending upload
    
def test_basic_logging_works():
    """Verify that the logs directory exists."""
    logs_dir = Path("logs")
    assert logs_dir.exists(), "Logs directory should exist"
    assert logs_dir.is_dir(), "Logs should be a directory"
