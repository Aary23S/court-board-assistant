from typing import List
from ..domain.routing import BoardRoutingResult
from ..domain.board_template import BoardTemplate
from ..domain.board_assembly import FinalBoard, FinalBoardSection, FinalBoardEntry

class FinalBoardAssembler:
    def __init__(self, template: BoardTemplate):
        self.template = template
        
    def assemble(self, routing_results: List[BoardRoutingResult], board_date: str = "") -> FinalBoard:
        board = FinalBoard(date=board_date)
        sections_map = {}
        
        for sec in self.template.sections:
            board_sec = FinalBoardSection(
                section_id=sec.id,
                section_name=sec.name,
                order=sec.order,
                entries=[]
            )
            board.sections.append(board_sec)
            sections_map[sec.id] = board_sec
            
        for r in routing_results:
            if r.routing_status != "ROUTED":
                continue
                
            for dest in r.destinations:
                if dest.section_id in sections_map:
                    entry = FinalBoardEntry(
                        case_number=r.source_case.cases or "",
                        party_name=r.source_case.party_name or "",
                        source_row_number=r.source_case.source_row_index,
                        registration_date=r.source_case.date_of_registration or "",
                        age=r.source_case.age or "",
                        readiness_status=r.source_case.ready_unready_stayed or "",
                        next_date=r.source_case.next_date or "",
                        next_purpose=r.source_case.next_purpose or "",
                        canonical_stage=r.canonical_stage,
                        on_same_stage_since=r.source_case.on_same_stage_since or "",
                        dormant_status=r.source_case.dormant_case_sine_die or "",
                        nature=r.source_case.nature or "",
                        delay_reason=r.source_case.delay_reason or "",
                        routing_reason=dest.routing_reason,
                        source_destination=dest,
                        optional_row_id=dest.row_id,
                        optional_row_name=dest.row_name
                    )
                    sections_map[dest.section_id].entries.append(entry)
                    
        for sec in board.sections:
            template_sec = next(s for s in self.template.sections if s.id == sec.section_id)
            row_order_map = {r.id: r.order for r in template_sec.rows}
            
            def sort_key(e: FinalBoardEntry):
                r_order = row_order_map.get(e.optional_row_id, 999999) if e.optional_row_id else 999999
                return (r_order, e.source_row_number)
                
            sec.entries.sort(key=sort_key)
            
        return board
