import pandas as pd
from pathlib import Path
from typing import List
from ..classification.collection import StageCollection
from ..domain.routing import BoardRoutingResult
from ..routing.prefix_extractor import CasePrefixExtractor

class StagewiseReviewRenderer:
    def __init__(self, stage_collection: StageCollection, routing_results: List[BoardRoutingResult]):
        self.stage_collection = stage_collection
        self.routing_results = routing_results
        self.prefix_extractor = CasePrefixExtractor()

    def render(self, output_path: str):
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # -------------------------------------------------------------
        # SHEET 1: Stagewise
        # -------------------------------------------------------------
        columns = [
            "Sr. No.", "Cases", "Party Name", "Date of Registration", "Age",
            "Ready / Unready / Stayed", "Next Date", "Next Purpose",
            "On same Stage since", "DORMANT CASE/SINE DIE CASE", "Nature", "Delay Reason"
        ]
        rows = []
        for stage_config, cases in self.stage_collection.get_all_stages():
            stage_header = [f"=== STAGE: {stage_config.canonical_name} ==="] + [""] * (len(columns) - 1)
            rows.append(stage_header)
            rows.append(columns)
            for result in cases:
                c = result.source_case
                row_data = [
                    c.sr_no or "",
                    c.cases or "",
                    c.party_name or "",
                    c.date_of_registration or "",
                    c.age or "",
                    c.ready_unready_stayed or "",
                    c.next_date or "",
                    c.next_purpose or "",
                    c.on_same_stage_since or "",
                    c.dormant_case_sine_die or "",
                    c.nature or "",
                    c.delay_reason or ""
                ]
                rows.append(row_data)
            rows.append([""] * len(columns))

        df_stagewise = pd.DataFrame(rows)

        # -------------------------------------------------------------
        # SHEET 2: Case Classification
        # -------------------------------------------------------------
        class_rows = []
        # Gather all classification results
        for _, cases in self.stage_collection.get_all_stages():
            for res in cases:
                c = res.source_case
                prefix = self.prefix_extractor.extract(c.cases or "")
                class_rows.append({
                    "Source Row": c.source_row_index,
                    "Case": c.cases or "",
                    "Party Name": c.party_name or "",
                    "Date of Registration": c.date_of_registration or "",
                    "Age": c.age or "",
                    "Ready / Unready / Stayed": c.ready_unready_stayed or "",
                    "Next Date": c.next_date or "",
                    "Next Purpose": c.next_purpose or "",
                    "Canonical Stage": res.canonical_stage or "UNMAPPED",
                    "Case Prefix": prefix,
                    "Nature": c.nature or "",
                    "Classification Status": res.classification_status
                })
        # Sort by Source Row for consistency
        class_rows.sort(key=lambda r: r["Source Row"])
        df_classification = pd.DataFrame(class_rows)

        # -------------------------------------------------------------
        # SHEET 3: Routing Review
        # -------------------------------------------------------------
        routing_rows = []
        for r in sorted(self.routing_results, key=lambda x: x.source_row_index):
            dests = [d.section_name for d in r.destinations]
            d1 = dests[0] if len(dests) > 0 else ""
            d2 = dests[1] if len(dests) > 1 else ""
            d3 = dests[2] if len(dests) > 2 else ""

            status = "RESOLVED" if r.routing_status == "ROUTED" else r.routing_status

            routing_rows.append({
                "Source Row": r.source_row_index,
                "Case": r.source_case.cases or "",
                "Canonical Stage": r.canonical_stage,
                "Ready / Unready / Stayed": r.readiness_status,
                "Case Prefix": r.case_prefix,
                "Destination 1": d1,
                "Destination 2": d2,
                "Destination 3": d3,
                "Routing Status": status,
                "Routing Reason": r.routing_reason
            })
        df_routing = pd.DataFrame(routing_rows)

        # Write to multi-sheet ODS
        try:
            with pd.ExcelWriter(str(path), engine='odf') as writer:
                df_stagewise.to_excel(writer, sheet_name='Stagewise', index=False, header=False)
                df_classification.to_excel(writer, sheet_name='Case Classification', index=False)
                df_routing.to_excel(writer, sheet_name='Routing Review', index=False)
        except Exception as e:
            raise RuntimeError(f"Failed to write multi-sheet stagewise review ODS: {e}")
