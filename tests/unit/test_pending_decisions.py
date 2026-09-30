import json
import pytest
from pathlib import Path

def test_pending_decisions_format():
    path = Path("config/pending_routing_decisions.json")
    assert path.exists(), "pending_routing_decisions.json must exist"
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert "decisions" in data
    assert isinstance(data["decisions"], list)
    assert len(data["decisions"]) == 2
    
    nbw_decision = next((d for d in data["decisions"] if d["id"] == "N-BW-UNREADY-ROUTING"), None)
    assert nbw_decision is not None
    assert nbw_decision["status"] == "PENDING_OFFICER_DECISION"
    assert "N.B.W._Unready" in nbw_decision["affected_stages"]
    
    ready_decision = next((d for d in data["decisions"] if d["id"] == "READY-UNREADY-STAGE"), None)
    assert ready_decision is not None
    assert ready_decision["status"] == "PENDING_OFFICER_DECISION"
    assert "Steps" in ready_decision["affected_stages"]
