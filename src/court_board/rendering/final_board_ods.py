import hashlib
from typing import List
from pathlib import Path

from odf.opendocument import OpenDocumentSpreadsheet
from odf.table import Table, TableColumn, TableRow, TableCell
from odf.text import P
from odf.style import Style, TextProperties, ParagraphProperties, TableColumnProperties

from ..domain.board_assembly import FinalBoard

class FinalBoardODSRenderer:
    def __init__(self, board: FinalBoard):
        self.board = board
        # Mapped from analyzing reference sample
        self.col_widths = [
            "4.6cm", "3.4cm", "4.4cm", "4.3cm", "3.5cm", "0.5cm", "0.7cm", 
            "2.6cm", "2.5cm", "3.0cm", "1.6cm", "2.7cm", "2.5cm", "4.6cm"
        ]

    def _create_styles(self, doc):
        self.styles = {}
        
        for i, w in enumerate(self.col_widths):
            style = Style(name=f"Col_{i}", family="table-column")
            style.addElement(TableColumnProperties(columnwidth=w))
            doc.automaticstyles.addElement(style)
            self.styles[f"Col_{i}"] = style

        bold_centered = Style(name="BoldCentered", family="table-cell")
        bold_centered.addElement(TextProperties(fontfamily="Calibri", fontsize="11pt", fontweight="bold"))
        bold_centered.addElement(ParagraphProperties(textalign="center"))
        doc.styles.addElement(bold_centered)
        self.styles["BoldCentered"] = bold_centered

        std_text = Style(name="StdText", family="table-cell")
        std_text.addElement(TextProperties(fontfamily="Calibri", fontsize="11pt"))
        doc.styles.addElement(std_text)
        self.styles["StdText"] = std_text

    def render(self, output_path: str):
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        doc = OpenDocumentSpreadsheet()
        self._create_styles(doc)
        
        date_str = self.board.date or "08.05.2026"  # Using sample's sheet date format if none provided
        # Convert date format if needed, but let's just use what's provided or a default
        table = Table(name=date_str)
        
        for i in range(14):
            table.addElement(TableColumn(stylename=self.styles[f"Col_{i}"]))
            
        # Row 1
        tr1 = TableRow()
        tc1 = TableCell(numbercolumnsspanned=4, valuetype="string")
        tc1.addElement(P(text=f"Date : {date_str}"))
        tr1.addElement(tc1)
        tc2 = TableCell(valuetype="string")
        tc2.addElement(P(text="Ready"))
        tr1.addElement(tc2)
        tr1.addElement(TableCell())
        tr1.addElement(TableCell())
        tc3 = TableCell(valuetype="string")
        tc3.addElement(P(text="Unready"))
        tr1.addElement(tc3)
        for _ in range(5):
            tr1.addElement(TableCell())
        tc4 = TableCell(valuetype="string")
        tc4.addElement(P(text=f"Date : {date_str}"))
        tr1.addElement(tc4)
        table.addElement(tr1)
        
        # Row 2
        tr2 = TableRow()
        tc = TableCell(valuetype="string"); tc.addElement(P(text="Took Seat at ")); tr2.addElement(tc)
        tc = TableCell(valuetype="string"); tc.addElement(P(text="11:00:00")); tr2.addElement(tc)
        tr2.addElement(TableCell())
        tc = TableCell(valuetype="string"); tc.addElement(P(text="Took Seat at ")); tr2.addElement(tc)
        tc = TableCell(valuetype="string"); tc.addElement(P(text="02:45:00")); tr2.addElement(tc)
        for _ in range(9): tr2.addElement(TableCell())
        table.addElement(tr2)
        
        # Row 3
        tr3 = TableRow()
        tc = TableCell(valuetype="string"); tc.addElement(P(text="Rise at ")); tr3.addElement(tc)
        tc = TableCell(valuetype="string"); tc.addElement(P(text="02:00:00")); tr3.addElement(tc)
        tr3.addElement(TableCell())
        tc = TableCell(valuetype="string"); tc.addElement(P(text="Rise at ")); tr3.addElement(tc)
        tc = TableCell(valuetype="string"); tc.addElement(P(text="05:45:00")); tr3.addElement(tc)
        for _ in range(9): tr3.addElement(TableCell())
        table.addElement(tr3)
        
        # Row 4: Empty
        table.addElement(TableRow())
        
        # Row 5: Column Headers
        tr5 = TableRow()
        headers = [
            ("Hearing", 1), ("Part Heard", 1), ("313.0", 1), ("Argument", 1), ("Judgement", 1),
            ("", 1), ("", 1), ("M.A.", 1), ("D.V.", 1), ("R.C.C.", 2), ("S.C.C.", 2), ("N.B.W. / B.W.", 1)
        ]
        for name, span in headers:
            tc = TableCell(stylename=self.styles["BoldCentered"], valuetype="string")
            if span > 1:
                tc.setAttribute("numbercolumnsspanned", str(span))
            if name:
                tc.addElement(P(text=name))
            tr5.addElement(tc)
        table.addElement(tr5)
        
        # Case data layout
        col_map = {
            "Hearing": 0, "Part Heard": 1, "313.0": 2, "Argument": 3, "Judgement": 4,
            "M.A.": 7, "D.V.": 8, "R.C.C.": 9, "S.C.C.": 11, "N.B.W. / B.W.": 13
        }
        span_map = {9: 2, 11: 2}
        
        case_lists = {idx: [] for idx in col_map.values()}
        
        for sec in self.board.sections:
            # For 313.0, we check standard name.
            name = sec.section_name
            if name == "313":
                name = "313.0"
                
            if name in col_map:
                idx = col_map[name]
                for e in sec.entries:
                    case_lists[idx].append(e.case_number)
                    
        max_rows = max([len(l) for l in case_lists.values()] + [0])
        
        for r_idx in range(max_rows):
            tr = TableRow()
            c_idx = 0
            while c_idx < 14:
                if c_idx in case_lists:
                    text = case_lists[c_idx][r_idx] if r_idx < len(case_lists[c_idx]) else ""
                    tc = TableCell(stylename=self.styles["StdText"], valuetype="string")
                    span = span_map.get(c_idx, 1)
                    if span > 1:
                        tc.setAttribute("numbercolumnsspanned", str(span))
                    if text:
                        tc.addElement(P(text=text))
                    tr.addElement(tc)
                    c_idx += span
                else:
                    tr.addElement(TableCell())
                    c_idx += 1
            table.addElement(tr)
            
        doc.spreadsheet.addElement(table)
        doc.save(str(path))
