# Template Resolution Finding: Section-Level Placement

## Analysis of Final Board Reference
An inspection of the original reference workbooks (`June 2026.xlsx` and `all stagewise.xlsx`) was performed to determine how stages like `N.B.W._Unready` are represented inside sections like `R.C.C.` and `S.C.C.`.

### Findings
1. **BoardSection**: A column header in the final daily board (e.g., "Hearing", "R.C.C.", "S.C.C.").
2. **BoardRow**: The template config defines `BoardRow` objects, but they do NOT physically appear as text labels or sub-headers in the daily board sheets.
3. **Stage-specific vs Section/Category Placement**: Because there are no row labels in the final output, cases are simply placed *directly* under the appropriate section column. The `BoardRow` definition merely acts as a sorting mechanism or logical bucket behind the scenes.
4. **Conclusion on Section-level Placement**: The final board expectations confirm that section placement **does not require an identical stage row**. Cases legitimately route to a section based on business rules, and if no explicit `BoardRow` exists for sorting, placing the case under the section (i.e. section-level placement) is sufficient and correct.

## Resolution
The routing engine's previous assumption that `destination section + source canonical stage` must always match an existing `BoardRow` was incorrect. We have updated the model and engine to allow `BoardDestination` to have `row_id=None` when an explicit row does not exist, enabling pure section-level placement.
