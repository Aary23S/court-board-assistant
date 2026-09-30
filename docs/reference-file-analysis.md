# Reference File Analysis

## Source Columns
The analysis of the reference file `01.07.2026.xlsx` reveals the following exact column headers:
1. `Sr. No.`
2. `Cases`
3. `Party Name`
4. `Date of Registration`
5. `Age`
6. `Ready / Unready / Stayed`
7. `Next Date`
8. `Next Purpose`
9. `On same Stage since`
10. `DORMANT CASE/SINE DIE CASE`
11. `Nature`
12. `Delay Reason`

## Distinct "Next Purpose" Values
(To be determined by the `inspect` CLI command). Initial observation shows values like:
- `N.B.W._Unready`
- `Evidence Part Heard`
- `N.B.W._Ready`
- `Depositing Amount`
- `Arguments`
- `Steps`
- `Order on Exh`

## Stage-wise Workbook Structure
The stage-wise workbook uses specific stage categories to group cases. This structural mapping will be implemented in a future phase.

## Final Board Sections
The final board representation is separated from the source data and will be implemented in a future phase based on Ready/Unready status and judicial stages.

## Important Formatting Characteristics
- The source files contain styling tags that can break legacy parsers (e.g., `openpyxl`). To avoid crashes and safely read the contents, robust parsers like `odfpy` (for ODS) and `calamine` (for XLSX) are required.
- The top rows contain title data, and the actual header row must be searched by looking for the `"Sr. No."` column.
- Row numbers from the source file must be maintained to ensure traceability.
