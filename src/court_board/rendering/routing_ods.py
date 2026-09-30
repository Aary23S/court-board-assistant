import pandas as pd
from pathlib import Path
from typing import List
from ..domain.routing import BoardRoutingResult

class RoutingReportRenderer:
    def __init__(self, results: List[BoardRoutingResult]):
        self.results = results

    def render(self, output_path: str):
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        routed = [r for r in self.results if r.routing_status == "ROUTED"]
        unresolved = [r for r in self.results if r.routing_status == "UNRESOLVED_ROUTING"]
        invalid = [r for r in self.results if r.routing_status == "INVALID_INPUT"]
        
        # 1. Summary Sheet
        summary_data = [
            ["Total Source Cases", len(self.results)],
            ["Routed", len(routed)],
            ["Unresolved", len(unresolved)],
            ["Invalid", len(invalid)]
        ]
        df_summary = pd.DataFrame(summary_data, columns=["Metric", "Count"])
        
        # 2. Routed Cases
        routed_data = []
        for r in routed:
            c = r.source_case
            routed_data.append({
                "Section": r.board_section,
                "Row Label": r.board_row,
                "Case": c.cases,
                "Party": c.party_name,
                "Stage": r.canonical_stage,
                "Ready/Unready": r.readiness_status
            })
        df_routed = pd.DataFrame(routed_data) if routed_data else pd.DataFrame(columns=["Section", "Row Label", "Case", "Party", "Stage", "Ready/Unready"])
        
        # 3. Unresolved Cases
        unresolved_data = []
        for r in unresolved:
            c = r.source_case
            unresolved_data.append({
                "Case": c.cases,
                "Stage": r.canonical_stage,
                "Ready/Unready": r.readiness_status,
                "Prefix": r.case_prefix,
                "Reason": r.routing_reason
            })
        df_unresolved = pd.DataFrame(unresolved_data) if unresolved_data else pd.DataFrame(columns=["Case", "Stage", "Ready/Unready", "Prefix", "Reason"])
        
        # 4. Invalid Cases
        invalid_data = []
        for r in invalid:
            c = r.source_case
            invalid_data.append({
                "Case": c.cases,
                "Stage": r.canonical_stage,
                "Reason": r.routing_reason
            })
        df_invalid = pd.DataFrame(invalid_data) if invalid_data else pd.DataFrame(columns=["Case", "Stage", "Reason"])
        
        engine = 'odf' if path.suffix.lower() == '.ods' else 'openpyxl'
        
        try:
            with pd.ExcelWriter(str(path), engine=engine) as writer:
                df_summary.to_excel(writer, sheet_name="Routing Summary", index=False)
                df_routed.to_excel(writer, sheet_name="Routed Cases", index=False)
                df_unresolved.to_excel(writer, sheet_name="Unresolved Cases", index=False)
                df_invalid.to_excel(writer, sheet_name="Invalid Cases", index=False)
        except Exception as e:
            raise RuntimeError(f"Failed to write routing report: {e}")
