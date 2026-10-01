from typing import List
from collections import Counter
from ..domain.routing import BoardRoutingResult
from ..domain.board_template import BoardTemplate
from ..domain.board_assembly import FinalBoard

class FinalBoardValidator:
    def __init__(self, template: BoardTemplate):
        self.template = template
        
    def validate(self, board: FinalBoard, routed_results: List[BoardRoutingResult]):
        # Section completeness & order
        if len(board.sections) != len(self.template.sections):
            raise ValueError(f"Section count mismatch: expected {len(self.template.sections)}, got {len(board.sections)}")
            
        for bs, ts in zip(board.sections, self.template.sections):
            if bs.section_id != ts.id:
                raise ValueError(f"Section order mismatch: expected {ts.id}, got {bs.section_id}")
            
        all_dests = []
        for r in routed_results:
            if r.routing_status == "ROUTED":
                for d in r.destinations:
                    all_dests.append((r.source_case.source_row_index, d.section_id, d.row_id))
                    
        all_entries = []
        for sec in board.sections:
            for e in sec.entries:
                all_entries.append((e.source_row_number, sec.section_id, e.optional_row_id))
                
        if len(all_entries) != len(all_dests):
            raise ValueError(f"Count mismatch: destinations={len(all_dests)}, entries={len(all_entries)}")
        
        if Counter(all_entries) != Counter(all_dests):
            raise ValueError("Destinations and entries mismatch (lost or unexpected elements)")
