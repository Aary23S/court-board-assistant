"""
HTML Template and Style Builder for Roznama PDF Generator.
Reproduces court-approved sample dimensions, borders, typography, and continuous flow.
Features:
- Compact repeated heading: 'प्रकरण क्रमांक: [case_number]' for every hearing.
- 3-column table: आजची दिनांक, दैनंदिन कामकाज तपशील, पुढे/निकाल तारीख.
- Line 1: Business description, Line 2: Stage (no literal 'Stage:' label).
- Dotted horizontal separator between hearings.
- Continuous pagination with no arbitrary page breaks.
"""
import html
from typing import Optional, List
from .font_manager import FontManager
from .presentation_model import RoznamaPresentationModel, HearingPresentationItem

class RoznamaHTMLBuilder:
    """
    Builds printable HTML strictly matching court-approved reference layout.
    """
    def __init__(self, font_manager: Optional[FontManager] = None):
        self.font_manager = font_manager or FontManager()

    def build_html_from_presentation(self, model: RoznamaPresentationModel) -> str:
        """
        Builds HTML from a canonical RoznamaPresentationModel.
        """
        font_b64 = self.font_manager.get_base64_font()
        sections_html = []
        total_items = len(model.items)

        for idx, item in enumerate(model.items):
            # Format Col 2: Business on line 1, Stage on line 2
            b_escaped = html.escape(item.business_text).replace("\n", "<br>")
            s_escaped = html.escape(item.stage_text).replace("\n", "<br>")

            if b_escaped and s_escaped:
                detail_html = f"<div class=\"business-desc\">{b_escaped}</div><div class=\"stage-desc\">{s_escaped}</div>"
            elif b_escaped:
                detail_html = f"<div class=\"business-desc\">{b_escaped}</div>"
            elif s_escaped:
                detail_html = f"<div class=\"stage-desc\">{s_escaped}</div>"
            else:
                detail_html = ""

            judge_display = html.escape(item.judge_designation or "न्यायाधीश")
            heading_escaped = html.escape(item.case_heading)
            is_last = (idx == total_items - 1)

            # Dotted separator between hearings (omitted after final hearing)
            separator_html = ""
            if not is_last:
                separator_html = '<div class="hearing-separator"></div>'

            section = f"""
            <div class="hearing-section">
                <div class="case-heading">{heading_escaped}</div>
                <table class="proceedings-table">
                    <thead>
                        <tr>
                            <th class="col-date">आजची दिनांक</th>
                            <th class="col-detail">दैनंदिन कामकाज तपशील</th>
                            <th class="col-next-date">पुढे/निकाल तारीख</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr class="record-row">
                            <td class="col-date">{html.escape(item.hearing_date)}</td>
                            <td class="col-detail">
                                <div class="detail-container">
                                    {detail_html}
                                    <div class="judge-signature">{judge_display}</div>
                                </div>
                            </td>
                            <td class="col-next-date">{html.escape(item.next_date)}</td>
                        </tr>
                    </tbody>
                </table>
                {separator_html}
            </div>
            """
            sections_html.append(section)

        body_content = "\n".join(sections_html)

        html_doc = f"""<!DOCTYPE html>
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

.hearing-section {{
    margin-bottom: 8px;
    page-break-inside: auto;
}}

/* Repeated Case Heading for Every Hearing */
.case-heading {{
    font-size: 10.5pt;
    font-weight: bold;
    margin-bottom: 4px;
    margin-top: 6px;
    color: #000;
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
    font-size: 10pt;
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

/* Column Width Ratios matching target_roznama_sample.pdf (94.7pt, 301.7pt, 113.8pt) */
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

.business-desc {{
    margin-bottom: 4px;
}}

.stage-desc {{
    margin-top: 2px;
}}

.judge-signature {{
    text-align: right;
    margin-top: 8px;
    font-weight: bold;
    font-size: 9pt;
}}

/* Dotted Horizontal Separator Between Hearing Sections */
.hearing-separator {{
    border-bottom: 1.2pt dotted #444;
    margin-top: 10px;
    margin-bottom: 8px;
    width: 100%;
}}

/* Clean Pagination: Avoid splitting single record rows if possible, but allow natural flow */
tr.record-row {{
    page-break-inside: avoid;
}}

thead {{
    display: table-header-group;
}}
</style>
</head>
<body>

{body_content}

</body>
</html>"""
        return html_doc

    def build_html(self, records: list, header=None) -> str:
        """
        Legacy compatibility adapter: builds presentation model on the fly if raw RoznamaRecord list passed.
        """
        model = RoznamaPresentationModel.from_state_records(
            transformed_records=records,
            source_records=[],
            human_edits={},
            header_case_number=header.case_number if header else None
        )
        return self.build_html_from_presentation(model)
