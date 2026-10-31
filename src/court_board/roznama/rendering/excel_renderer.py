"""
Excel (XLSX) Renderer for Court-Approved Roznama Proceedings.
Produces professionally formatted, LibreOffice Calc-compatible spreadsheets
matching the visual 3-column table structure and dotted section separators.
"""
from pathlib import Path
from typing import Union, List, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from ..domain.models import RoznamaRecord, RoznamaHeader
from .presentation_model import RoznamaPresentationModel

class RoznamaExcelRenderer:
    """
    Renders RoznamaPresentationModel into a court-formatted Excel (.xlsx) workbook.
    """
    def __init__(self):
        pass

    def render(
        self,
        presentation_model: Union[RoznamaPresentationModel, List[RoznamaRecord]],
        output_path: Union[str, Path],
        header: Optional[RoznamaHeader] = None
    ) -> Path:
        """
        Renders the presentation model into an Excel workbook at output_path.
        """
        if not isinstance(presentation_model, RoznamaPresentationModel):
            presentation_model = RoznamaPresentationModel.from_state_records(
                transformed_records=presentation_model,
                source_records=[],
                human_edits={},
                header_case_number=header.case_number if header else None
            )

        out_path = Path(output_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Roznama"
        ws.views.sheetView[0].showGridLines = True

        # Styles definition
        font_name = "Lohit Devanagari"
        fallback_font = "Segoe UI"

        heading_font = Font(name=font_name, size=11, bold=True, color="000000")
        th_font = Font(name=font_name, size=10, bold=True, color="000000")
        td_font = Font(name=font_name, size=9.5, bold=False, color="000000")
        judge_font = Font(name=font_name, size=9, bold=True, color="000000")

        th_fill = PatternFill(start_color="F5F5F5", end_color="F5F5F5", fill_type="solid")

        thin_side = Side(border_style="thin", color="000000")
        cell_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
        
        # Dotted bottom border for the hearing separator
        dotted_side = Side(border_style="dotted", color="666666")
        separator_border = Border(bottom=dotted_side)

        current_row = 1
        total_items = len(presentation_model.items)

        for idx, item in enumerate(presentation_model.items):
            # 1. Case Identification Heading Row
            ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=3)
            h_cell = ws.cell(row=current_row, column=1, value=item.case_heading)
            h_cell.font = heading_font
            h_cell.alignment = Alignment(horizontal="left", vertical="center")
            ws.row_dimensions[current_row].height = 24
            current_row += 1

            # 2. Table Header Row (3 columns)
            headers = ["आजची दिनांक", "दैनंदिन कामकाज तपशील", "पुढे/निकाल तारीख"]
            for col_num, text in enumerate(headers, start=1):
                c = ws.cell(row=current_row, column=col_num, value=text)
                c.font = th_font
                c.fill = th_fill
                c.border = cell_border
                c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            ws.row_dimensions[current_row].height = 22
            current_row += 1

            # 3. Proceedings Data Row
            # Col 1: Date
            c_date = ws.cell(row=current_row, column=1, value=item.hearing_date)
            c_date.font = td_font
            c_date.border = cell_border
            c_date.alignment = Alignment(horizontal="center", vertical="top")

            # Col 2: Business (Line 1) + Stage (Line 2) + Judge designation
            # Avoid literal 'Stage:'
            combined_text = item.combined_detail
            if item.judge_designation:
                combined_text = f"{combined_text}\n\n{item.judge_designation}"

            c_detail = ws.cell(row=current_row, column=2, value=combined_text)
            c_detail.font = td_font
            c_detail.border = cell_border
            c_detail.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)

            # Col 3: Next Date
            c_next = ws.cell(row=current_row, column=3, value=item.next_date)
            c_next.font = td_font
            c_next.border = cell_border
            c_next.alignment = Alignment(horizontal="center", vertical="top")

            # Dynamic row height estimation based on lines
            line_count = combined_text.count("\n") + max(1, len(combined_text) // 60)
            ws.row_dimensions[current_row].height = max(40, line_count * 16)
            current_row += 1

            # 4. Dotted Separator Row between consecutive hearings (omit after final)
            if idx < total_items - 1:
                # Blank row with dotted bottom border across columns 1 to 3
                for col_num in range(1, 4):
                    sep_c = ws.cell(row=current_row, column=col_num, value="")
                    sep_c.border = separator_border
                ws.row_dimensions[current_row].height = 10
                current_row += 1
                # Small spacer row
                ws.row_dimensions[current_row].height = 8
                current_row += 1

        # Set Column Widths (matching PDF ratios ~ 18.6%, 59.1%, 22.3%)
        ws.column_dimensions["A"].width = 16  # Col 1
        ws.column_dimensions["B"].width = 65  # Col 2
        ws.column_dimensions["C"].width = 18  # Col 3

        wb.save(str(out_path))
        return out_path

