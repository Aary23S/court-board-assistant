import json
from typing import List, Dict, Tuple, Set
from pathlib import Path

from ..domain.models import CaseRecord
from ..domain.routing import BoardRoutingResult, BoardDestination
from ..domain.board_template import BoardTemplate, BoardSection, BoardRow
from .prefix_extractor import CasePrefixExtractor

class RoutingEngine:
    def __init__(
        self, 
        template_path: str = "config/final_board_template.json",
        stages_path: str = "config/stages.json"
    ):
        self.template = self._load_template(template_path)
        self.canonical_stages = self._load_canonical_stages(stages_path)
        self.prefix_extractor = CasePrefixExtractor()
        
    def _load_template(self, path: str) -> BoardTemplate:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Template config not found at {p}")
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return BoardTemplate(**data)
            
    def _load_canonical_stages(self, path: str) -> set:
        p = Path(path)
        if not p.exists():
            return set()
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {s["canonical_name"] for s in data}

    def _find_row_in_section(self, section_name: str, canonical_stage: str) -> List[BoardDestination]:
        for sec in self.template.sections:
            if sec.name == section_name:
                matches = [r for r in sec.rows if r.canonical_stage_reference == canonical_stage]
                if len(matches) == 1:
                    row = matches[0]
                    return [BoardDestination(
                        section_id=sec.id,
                        section_name=sec.name,
                        row_id=row.id,
                        row_name=row.display_label,
                        source_stage=canonical_stage,
                        routing_reason=f"Matched stage '{canonical_stage}' in section '{section_name}'"
                    )]
                elif len(matches) > 1:
                    return []
                else:
                    return [BoardDestination(
                        section_id=sec.id,
                        section_name=sec.name,
                        row_id=None,
                        row_name=None,
                        source_stage=canonical_stage,
                        routing_reason=f"Section-level placement in '{section_name}'"
                    )]
        return []
        
    def _get_generic_hearing_destination(self, source_stage: str) -> List[BoardDestination]:
        for sec in self.template.sections:
            if sec.name == "Hearing":
                matches = [r for r in sec.rows if r.canonical_stage_reference == "Hearing"]
                if len(matches) == 1:
                    row = matches[0]
                    return [BoardDestination(
                        section_id=sec.id,
                        section_name=sec.name,
                        row_id=row.id,
                        row_name=row.display_label,
                        source_stage=source_stage,
                        routing_reason="Ready cases are placed in Hearing."
                    )]
        return []

    def _normalize_readiness(self, status: str) -> str:
        if not status:
            return ""
        status = status.upper().strip()
        if status == "R": return "Ready"
        if status == "U": return "Unready"
        if status == "S": return "Stayed"
        return status.capitalize()

    def route(self, case: CaseRecord, canonical_stage: str) -> BoardRoutingResult:
        prefix = self.prefix_extractor.extract(case.cases or "")
        ready_status = self._normalize_readiness(case.ready_unready_stayed)
        
        base_result = {
            "source_case": case,
            "source_row_index": case.source_row_index,
            "canonical_stage": canonical_stage,
            "readiness_status": ready_status,
            "case_prefix": prefix
        }

        # 1. Invalid Input Check
        if canonical_stage not in self.canonical_stages:
            return BoardRoutingResult(
                **base_result,
                routing_status="INVALID_INPUT",
                routing_reason=f"Unknown canonical stage: '{canonical_stage}'"
            )

        # 2. Stayed Cases
        if ready_status == "Stayed":
            return BoardRoutingResult(
                **base_result,
                routing_status="UNRESOLVED_ROUTING",
                routing_reason="Stayed status has no approved routing rule"
            )

        # 3. Ready Routing
        if ready_status == "Ready":
            dests = self._get_generic_hearing_destination(canonical_stage)
            if not dests:
                return BoardRoutingResult(
                    **base_result,
                    routing_status="UNRESOLVED_ROUTING",
                    routing_reason="Generic 'Hearing' row not found in template"
                )
                
            return BoardRoutingResult(
                **base_result,
                destinations=dests,
                routing_status="ROUTED",
                routing_reason="Successfully routed to Hearing"
            )

        # 4. Unready Routing
        if ready_status == "Unready":
            if prefix == "UNKNOWN_PREFIX":
                return BoardRoutingResult(
                    **base_result,
                    routing_status="UNRESOLVED_ROUTING",
                    routing_reason="Unknown case prefix for Unready routing"
                )
                
            is_warrant = canonical_stage in ["N.B.W._Unready", "B.W._Unready"]
            target_sections = []
            routing_desc = ""
            
            if prefix == "Cri.M.A.":
                target_sections.append("M.A.")
                if is_warrant:
                    target_sections.append("N.B.W. / B.W.")
                    routing_desc = "Unready Cri.M.A. N.B.W./B.W. case routed to M.A. and N.B.W./B.W."
                else:
                    routing_desc = "Unready Cri.M.A. case routed to M.A."
            elif prefix == "PWDVA Appln.":
                target_sections.append("D.V.")
                if is_warrant:
                    target_sections.append("N.B.W. / B.W.")
                    routing_desc = "Unready PWDVA Appln. N.B.W./B.W. case routed to D.V. and N.B.W./B.W."
                else:
                    routing_desc = "Unready PWDVA Appln. case routed to D.V."
            elif prefix in ["R.C.C.", "S.C.C."]:
                target_sections.extend(["R.C.C.", "S.C.C."])
                if is_warrant:
                    target_sections.append("N.B.W. / B.W.")
                    routing_desc = f"Unready {prefix} N.B.W./B.W. case routed to R.C.C., S.C.C., and N.B.W./B.W."
                else:
                    routing_desc = f"Unready {prefix} case routed to R.C.C. and S.C.C."
            
            # Look up each destination
            final_dests = []
            seen_dests = set()
            
            for sec_name in target_sections:
                dests = self._find_row_in_section(sec_name, canonical_stage)
                if not dests:
                    return BoardRoutingResult(
                        **base_result,
                        routing_status="UNRESOLVED_ROUTING",
                        routing_reason=f"Stage '{canonical_stage}' not found in required section '{sec_name}'"
                    )
                dest = dests[0]
                dest.routing_reason = routing_desc
                
                ident = (dest.section_id, dest.row_id)
                if ident not in seen_dests:
                    seen_dests.add(ident)
                    final_dests.append(dest)
                    
            if not final_dests:
                return BoardRoutingResult(
                    **base_result,
                    routing_status="UNRESOLVED_ROUTING",
                    routing_reason="No valid destinations found"
                )
                
            return BoardRoutingResult(
                **base_result,
                destinations=final_dests,
                routing_status="ROUTED",
                routing_reason="Successfully routed to Unready sections"
            )

        # 5. Unknown/Empty Readiness
        return BoardRoutingResult(
            **base_result,
            routing_status="UNRESOLVED_ROUTING",
            routing_reason=f"Unrecognized or missing readiness status: '{ready_status}'"
        )
