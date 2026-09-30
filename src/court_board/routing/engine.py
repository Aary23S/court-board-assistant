import json
from typing import List, Dict, Tuple
from pathlib import Path

from ..domain.models import CaseRecord
from ..domain.routing import BoardRoutingResult
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
        
        # Hardcoded Officer Rules (A, B, C, D)
        self.unready_prefix_to_section = {
            "Cri.M.A.": "M.A.",
            "PWDVA Appln.": "D.V.",
            "R.C.C.": "R.C.C.",
            "S.C.C.": "S.C.C."
        }

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

    def _find_rows_in_section(self, section_name: str, canonical_stage: str) -> List[BoardRow]:
        for sec in self.template.sections:
            if sec.name == section_name:
                return [r for r in sec.rows if r.canonical_stage_reference == canonical_stage]
        return []

    def _find_rows_by_side(self, ready_side: bool, canonical_stage: str) -> List[Tuple[BoardSection, BoardRow]]:
        matches = []
        target_behavior = "READY" if ready_side else "UNREADY"
        
        for sec in self.template.sections:
            if sec.ready_unready_behavior == target_behavior:
                for r in sec.rows:
                    if r.canonical_stage_reference == canonical_stage:
                        matches.append((sec, r))
        return matches

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
            "case_prefix": prefix,
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
            matches = self._find_rows_by_side(ready_side=True, canonical_stage=canonical_stage)
            
            if len(matches) == 1:
                sec, row = matches[0]
                return BoardRoutingResult(
                    **base_result,
                    board_section=sec.name,
                    board_row=row.display_label,
                    routing_status="ROUTED",
                    routing_reason="Unique match on Ready side"
                )
            elif len(matches) == 0:
                return BoardRoutingResult(
                    **base_result,
                    routing_status="UNRESOLVED_ROUTING",
                    routing_reason="0 matching rows on Ready side"
                )
            else:
                return BoardRoutingResult(
                    **base_result,
                    routing_status="UNRESOLVED_ROUTING",
                    routing_reason=f"Multiple matches ({len(matches)}) on Ready side"
                )

        # 4. Unready Routing
        if ready_status == "Unready":
            if prefix == "UNKNOWN_PREFIX":
                return BoardRoutingResult(
                    **base_result,
                    routing_status="UNRESOLVED_ROUTING",
                    routing_reason="Unknown case prefix for Unready routing"
                )
                
            target_section_name = self.unready_prefix_to_section.get(prefix)
            if not target_section_name:
                return BoardRoutingResult(
                    **base_result,
                    routing_status="UNRESOLVED_ROUTING",
                    routing_reason=f"Prefix '{prefix}' has no approved section mapping"
                )
                
            matches = self._find_rows_in_section(target_section_name, canonical_stage)
            if len(matches) == 1:
                return BoardRoutingResult(
                    **base_result,
                    board_section=target_section_name,
                    board_row=matches[0].display_label,
                    routing_status="ROUTED",
                    routing_reason="Unique match in unready section"
                )
            elif len(matches) == 0:
                return BoardRoutingResult(
                    **base_result,
                    routing_status="UNRESOLVED_ROUTING",
                    routing_reason=f"Stage '{canonical_stage}' not found in section '{target_section_name}'"
                )
            else:
                return BoardRoutingResult(
                    **base_result,
                    routing_status="UNRESOLVED_ROUTING",
                    routing_reason=f"Multiple matches in section '{target_section_name}'"
                )

        # 5. Unknown/Empty Readiness
        return BoardRoutingResult(
            **base_result,
            routing_status="UNRESOLVED_ROUTING",
            routing_reason=f"Unrecognized or missing readiness status: '{ready_status}'"
        )
