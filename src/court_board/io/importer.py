import pandas as pd
from typing import List, Tuple, Dict, Any
from pathlib import Path
from ..domain.models import CaseRecord, ValidationResult

REQUIRED_COLUMNS = [
    "Cases",
    "Next Purpose"
]

class CourtBoardImporter:
    """Read-only importer for the daily court ODS/XLSX."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.records: List[CaseRecord] = []
        self.validations: List[ValidationResult] = []
        self.header_index = -1
        self.columns: List[str] = []

    def _add_error(self, message: str, row_index: int = None, column: str = None):
        self.validations.append(ValidationResult(status="ERROR", message=message, source_row_index=row_index, column=column))

    def _add_warning(self, message: str, row_index: int = None, column: str = None):
        self.validations.append(ValidationResult(status="WARNING", message=message, source_row_index=row_index, column=column))

    def load(self) -> Tuple[List[CaseRecord], List[ValidationResult]]:
        """Loads the spreadsheet, parses cases, and validates."""
        if not self.file_path.exists():
            self._add_error(f"File not found: {self.file_path}")
            return [], self.validations

        # Use odfpy for .ods, calamine for .xlsx to avoid styling crashes
        engine = 'calamine' if self.file_path.suffix.lower() == '.xlsx' else 'odf'
        try:
            df = pd.read_excel(self.file_path, engine=engine, header=None)
        except Exception as e:
            self._add_error(f"Failed to read file: {str(e)}")
            return [], self.validations

        # Find header row
        for idx, row in df.iterrows():
            if row.astype(str).str.contains('Sr. No.', case=False).any():
                self.header_index = idx
                break

        if self.header_index == -1:
            self._add_error("Could not locate the header row (missing 'Sr. No.').")
            return [], self.validations

        self.columns = [str(c).strip() if pd.notna(c) else f"Unnamed_{i}" for i, c in enumerate(df.iloc[self.header_index])]

        # Validate required columns
        for req_col in REQUIRED_COLUMNS:
            if req_col not in self.columns:
                self._add_error(f"Required column missing: '{req_col}'")
                
        if any(v.status == "ERROR" for v in self.validations):
            return [], self.validations

        # Parse rows
        for idx in range(self.header_index + 1, len(df)):
            row = df.iloc[idx]
            raw_dict = {col: row.iloc[i] for i, col in enumerate(self.columns)}
            
            # Check for empty row
            if all(pd.isna(val) or str(val).strip() == "" for val in raw_dict.values()):
                self._add_warning("Empty case row found and skipped.", row_index=idx)
                continue
                
            self._process_row(idx, raw_dict)

        return self.records, self.validations

    def _get_val(self, raw_dict: Dict[str, Any], col_name: str) -> str:
        val = raw_dict.get(col_name)
        return str(val).strip() if pd.notna(val) and str(val).strip() else None

    def _process_row(self, idx: int, raw_dict: Dict[str, Any]):
        cases = self._get_val(raw_dict, "Cases")
        next_purpose = self._get_val(raw_dict, "Next Purpose")

        if not cases:
            self._add_error("Missing case number.", row_index=idx, column="Cases")
            return
            
        if not next_purpose:
            self._add_error("Missing Next Purpose.", row_index=idx, column="Next Purpose")
            return
            
        ready = self._get_val(raw_dict, "Ready / Unready / Stayed")
        if ready and ready not in ["R", "U", "S"]:
            self._add_warning(f"Unknown Ready/Unready value: {ready}", row_index=idx, column="Ready / Unready / Stayed")

        record = CaseRecord(
            source_row_index=idx,
            sr_no=self._get_val(raw_dict, "Sr. No."),
            cases=cases,
            party_name=self._get_val(raw_dict, "Party Name"),
            date_of_registration=self._get_val(raw_dict, "Date of Registration"),
            age=self._get_val(raw_dict, "Age"),
            ready_unready_stayed=ready,
            next_date=self._get_val(raw_dict, "Next Date"),
            next_purpose=next_purpose,
            on_same_stage_since=self._get_val(raw_dict, "On same Stage since"),
            dormant_case_sine_die=self._get_val(raw_dict, "DORMANT CASE/SINE DIE CASE"),
            nature=self._get_val(raw_dict, "Nature"),
            delay_reason=self._get_val(raw_dict, "Delay Reason"),
            raw_values=raw_dict
        )
        self.records.append(record)
        self.validations.append(ValidationResult(status="VALID", message="Valid case record", source_row_index=idx))
