# Final Board Template Discrepancy Report

## 1. Exact Structural Discrepancy
The officer-confirmed business rules route Unready `N.B.W._Unready` and `B.W._Unready` cases to multiple destination sections simultaneously (e.g., an R.C.C. warrant case routes to `R.C.C.`, `S.C.C.`, and `N.B.W. / B.W.`). However, the final board template requires a specific `BoardRow` for placement within a section, and the stages `N.B.W._Unready` and `B.W._Unready` do NOT exist as rows within the `R.C.C.`, `S.C.C.`, `M.A.`, or `D.V.` sections. 

## 2. Relevant Template Sections/Rows
In `config/final_board_template.json`, the `R.C.C.` section contains the following rows related to warrants or unready stages:
- `Awaiting Warrant` (canonical_stage_reference: "Awaiting Warrant")
- `Unready Board` (canonical_stage_reference: "Unready Board")

It does **not** contain rows for `N.B.W._Unready` or `B.W._Unready`. 
Similarly, the `M.A.` section completely lacks any warrant-related row.

## 3. Why the Officer-Confirmed Rule Cannot Currently Be Represented
The current routing engine logic maps the `source canonical stage` to a row with a matching `canonical_stage_reference`. Because the template does not contain `N.B.W._Unready` as a row within `R.C.C.` or `M.A.`, the engine correctly reports 0 matching rows and falls back to `UNRESOLVED_ROUTING`. 

We cannot safely fallback to "section-level only placement" (where `row_id=None`) because it is highly likely these cases belong under a specific print header on the physical board (e.g., an explicit "N.B.W." sub-heading under R.C.C., or grouped into "Awaiting Warrant"). Silently omitting the row would compromise the final board presentation.

## 4. Proposed Minimum Structural Template Change
We must modify the `BoardRow` definition in the template to support mapping **multiple** canonical stages to a single display row, or we must explicitly add the missing rows. 

**Proposal A (If they belong under their own explicit headings):**
Add new `BoardRow` objects to `R.C.C.`, `S.C.C.`, `M.A.`, and `D.V.` for `N.B.W._Unready` and `B.W._Unready`.

**Proposal B (If they belong under "Awaiting Warrant" or generic headings):**
Change `canonical_stage_reference: str` to `canonical_stage_references: List[str]` in the template. For example, update the `Awaiting Warrant` row in `R.C.C.` to map to `["Awaiting Warrant", "N.B.W._Unready", "B.W._Unready"]`. 

*(We will use Proposal A as the minimum structural change for the test, explicitly adding the rows to the template, pending officer visual confirmation).*
