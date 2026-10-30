"""
HTML Template and Style Builder for Roznama PDF Generator.
Reproduces target_roznama_sample.pdf dimensions, borders, and typography.
"""
from typing import List, Optional
from ..domain.models import RoznamaRecord, RoznamaHeader
from .font_manager import FontManager

class RoznamaHTMLBuilder:
    """
    Builds printable HTML matching target_roznama_sample.pdf specifications.
    """
    def __init__(self, font_manager: Optional[FontManager] = None):
        self.font_manager = font_manager or FontManager()

    def build_html(self, records: List[RoznamaRecord], header: Optional[RoznamaHeader] = None) -> str:
        font_b64 = self.font_manager.get_base64_font()
        h = header or RoznamaHeader()

        # Build table rows
        rows_html = []
        for r in records:
            next_date_display = r.next_date if r.next_date else ""
            judge_display = r.judge_designation if r.judge_designation else "न्यायाधीश"

            rows_html.append(f"""
            <tr class="record-row">
                <td class="col-date">{r.today_date}</td>
                <td class="col-detail">
                    <div class="detail-text">{r.proceedings_detail}</div>
                    <div class="judge-signature">{judge_display}</div>
                </td>
                <td class="col-next-date">{next_date_display}</td>
            </tr>
            """)

        table_rows = "\n".join(rows_html)

        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@font-face {{
    font-family: 'Lohit Devanagari';
    src: url('data:font/truetype;charset=utf-8;base64,{font_b64}') format('truetype');
    font-weight: normal;
    font-style: normal;
}}

@page {{
    size: A4 portrait;
    margin-top: 15mm;
    margin-bottom: 15mm;
    margin-left: 20mm;
    margin-right: 10mm;
}}

body {{
    font-family: 'Lohit Devanagari', 'Noto Serif Devanagari', serif;
    font-size: 10pt;
    line-height: 1.35;
    color: #000;
    margin: 0;
    padding: 0;
}}

/* Header Banner Section */
.court-header {{
    text-align: center;
    margin-bottom: 8px;
}}
.judge-title {{
    font-size: 11pt;
    font-weight: bold;
    margin-bottom: 4px;
}}
.case-info-grid {{
    width: 100%;
    margin-bottom: 8px;
    font-size: 10pt;
}}
.case-info-grid td {{
    padding: 2px 0;
    vertical-align: top;
}}

/* Table Layout (Exactly 3 Columns) */
.proceedings-table {{
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
    border: 0.5pt solid #000;
}}

.proceedings-table th {{
    border: 0.5pt solid #000;
    padding: 4px;
    font-size: 10.5pt;
    font-weight: bold;
    text-align: center;
    background-color: #fafafa;
}}

.proceedings-table td {{
    border: 0.5pt solid #000;
    padding: 6px 5px;
    vertical-align: top;
    word-wrap: break-word;
}}

/* Column Width Ratios */
.col-date {{
    width: 18.6%;
    text-align: center;
    font-size: 10pt;
}}

.col-detail {{
    width: 59.1%;
    text-align: justify;
    font-size: 9.5pt;
}}

.col-next-date {{
    width: 22.3%;
    text-align: center;
    font-size: 10pt;
}}

.judge-signature {{
    text-align: right;
    margin-top: 12px;
    font-weight: bold;
    font-size: 9pt;
}}

/* Pagination & Page Breaks */
tr.record-row {{
    page-break-inside: avoid;
}}

thead {{
    display: table-header-group;
}}
</style>
</head>
<body>

<div class="court-header">
    <div class="judge-title">
        {h.judge_name or "श्री. जे. व्ही. पालीवाल"}<br>
        १३ वे सह दिवाणी न्यायाधीश वरिष्ठ स्तर तथा अति. मुख्य न्यायदंडाधिकारी, नाशिक यांचे न्यायालयात
    </div>
</div>

<table class="case-info-grid">
    <tr>
        <td style="width: 55%;"><strong>प्रकरण क्रमांक:</strong> {h.case_number or "---"}</td>
        <td style="width: 45%;"><strong>सीएनआर क्रमांक:</strong> {h.cnr_number or "---"}</td>
    </tr>
    <tr>
        <td colspan="2"><strong>पक्षकार:</strong> {h.parties or "सरकार तर्फे पोस्टे वि. आरोपी"}</td>
    </tr>
    <tr>
        <td colspan="2"><strong>सहाय्यक सरकारी अभियोक्ता / वकील:</strong> {h.app_advocate or "---"}</td>
    </tr>
</table>

<table class="proceedings-table">
    <thead>
        <tr>
            <th class="col-date">आजची दिनांक</th>
            <th class="col-detail">दैनंदिन कामकाज तपशील</th>
            <th class="col-next-date">पुढे/निकाल तारीख</th>
        </tr>
    </thead>
    <tbody>
        {table_rows}
    </tbody>
</table>

</body>
</html>"""
        return html

