"""
Roznama Transformation Engine implementing Business Rules A, B, C, and D.
Converts SourceProceedingRecord instances into RoznamaRecord instances.
"""
from typing import List, Optional
from ..domain.models import SourceProceedingRecord, RoznamaRecord

class RoznamaTransformer:
    """
    Transforms extracted source proceeding records into 3-column Roznama records:
      - Rule A: Combines Business & Stage into '[Business]. Stage: [Stage]'
      - Rule B: Maps source hearing_date -> today_date
      - Rule C: Maps next_date to records[i+1].hearing_date; None for final
      - Rule D: Strictly preserves source appearance order (record_sequence)
    """

    @classmethod
    def format_proceedings_detail(cls, business: str, stage: str) -> str:
        """
        Public API: Combines Business content and Stage value into one proceedings detail string (Rule A).
        Avoids double periods if business text already ends with punctuation.
        """
        b_clean = business.strip() if business else ""
        s_clean = stage.strip() if stage else ""

        if not b_clean and not s_clean:
            return ""
        if not s_clean:
            return b_clean
        if not b_clean:
            return f"Stage: {s_clean}"

        # If business already ends with '.', '!', '?', or '|', do not append another period
        if b_clean[-1] in [".", "!", "?", "|", "।"]:
            return f"{b_clean} Stage: {s_clean}"
        else:
            return f"{b_clean}. Stage: {s_clean}"

    @classmethod
    def _format_proceedings_detail(cls, business: str, stage: str) -> str:
        """Deprecated alias preserved for backward compatibility."""
        return cls.format_proceedings_detail(business, stage)

    def transform(self, records: List[SourceProceedingRecord]) -> List[RoznamaRecord]:
        """
        Transforms a list of SourceProceedingRecord objects into RoznamaRecord objects.
        Validates sequential integrity and applies Rules A, B, C, and D.
        """
        if not records:
            return []

        # Validate sequence integrity: check for duplicate or non-positive sequence numbers
        seen_seq = set()
        for idx, rec in enumerate(records):
            if rec.record_sequence in seen_seq:
                raise ValueError(
                    f"Duplicate record_sequence '{rec.record_sequence}' detected at index {idx}."
                )
            if rec.record_sequence <= 0:
                raise ValueError(
                    f"Invalid record_sequence '{rec.record_sequence}' at index {idx}. Must be positive."
                )
            seen_seq.add(rec.record_sequence)

        roznama_records: List[RoznamaRecord] = []
        total = len(records)

        for i in range(total):
            source_rec = records[i]
            
            # Rule B: Map hearing_date -> today_date
            today_date = source_rec.hearing_date

            # Rule A: Format combined proceedings detail
            proceedings_detail = self._format_proceedings_detail(
                source_rec.business, source_rec.stage
            )

            # Rule C: Next date is hearing_date of records[i+1]; None for final record
            if i < total - 1:
                next_date = records[i + 1].hearing_date
            else:
                next_date = None

            roznama_rec = RoznamaRecord(
                record_sequence=source_rec.record_sequence,
                today_date=today_date,
                proceedings_detail=proceedings_detail,
                next_date=next_date,
                judge_designation="न्यायाधीश"
            )
            roznama_records.append(roznama_rec)

        return roznama_records

