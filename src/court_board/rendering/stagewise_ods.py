import pandas as pd
from pathlib import Path
from ..classification.collection import StageCollection

class StageWiseRenderer:
    def __init__(self, collection: StageCollection):
        self.collection = collection
        self.columns = [
            "Sr. No.",
            "Cases",
            "Party Name",
            "Date of Registration",
            "Age",
            "Ready / Unready / Stayed",
            "Next Date",
            "Next Purpose",
            "On same Stage since",
            "DORMANT CASE/SINE DIE CASE",
            "Nature",
            "Delay Reason"
        ]

    def render(self, output_path: str):
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        rows = []
        for stage_config, cases in self.collection.get_all_stages():
            # Stage Header
            stage_header = [f"=== STAGE: {stage_config.canonical_name} ==="] + [""] * (len(self.columns) - 1)
            rows.append(stage_header)
            
            # Column Headers
            rows.append(self.columns)
            
            # Cases
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
            
            # Blank row spacing
            rows.append([""] * len(self.columns))

        df = pd.DataFrame(rows)
        
        # Determine engine based on extension
        engine = 'odf' if path.suffix.lower() == '.ods' else 'openpyxl'
        
        try:
            df.to_excel(str(path), index=False, header=False, engine=engine)
        except Exception as e:
            raise RuntimeError(f"Failed to write ODS/XLSX file: {e}")
