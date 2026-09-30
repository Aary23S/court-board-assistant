# Domain Understanding

## 1. What the source file represents
The source file is a daily extract (an `.ods` or `.xlsx` spreadsheet) from an existing court system containing a list of all case records scheduled for a given day.

## 2. Why it is the source of truth
The court's central system produces this document. All data regarding cases, participants, stages, and hearing purposes in this file represents the official record. Any modification to this file undermines the integrity of the official court data.

## 3. What Next Purpose represents
The "Next Purpose" column contains the primary indicator of why a case is listed on the board. It is the key to identifying the procedural stage of the case (e.g., arguments, framing of issues, evidence, etc.).

## 4. What stage-wise filtering means
Stage-wise filtering is the process of reading each case from the source file, examining its "Next Purpose" (and potentially other metadata), and classifying it into an exact judicial stage category. Cases with identical procedural stages are grouped together.

## 5. What the final board represents
The final court board is a formatted, structured document that organizes cases according to the court's customary layout, separating them by their stage-wise classifications and applying specific presentation rules (such as Ready/Unready requirements). 

## 6. Difference between source data and generated presentation
Source data is the raw, unformatted, and unfiltered representation of case records exactly as provided by the court system. Generated presentation is a separate, structured document derived from the source data, tailored for the court officer's workflow. It involves formatting, grouping, and visual enhancements without altering the underlying raw data.

## 7. Why original source files must never be modified
Modifying the original source file breaks the chain of custody of the data. If an error occurs in the automation, it becomes impossible to determine if the error came from the court system's source data or the application's modifications. Treating source files as read-only ensures reproducibility and auditability.

## 8. Linux/Ubuntu + LibreOffice requirement
The end-users or target system for this application runs on Linux (Ubuntu) using LibreOffice for spreadsheet tasks. The solution must natively handle OpenDocument Spreadsheet (`.ods`) files without relying on proprietary Microsoft Excel APIs or cloud services. 

## 9. Current known uncertainties
- The exact column names in the source files are currently unknown because the sample files have not been provided yet.
- The precise list of "Next Purpose" values and how they map to stage-wise categories is unknown.
- The structural layout of the "stage-wise workbook" and the "final board" are unknown.
- The specific definitions and formatting rules for "Ready/Unready" are unknown.
