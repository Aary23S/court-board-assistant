# Case-to-Board Routing Discovery

This report investigates what source information is required to route an individual case to the correct BoardRow within the Final Board Template.

## A. Source fields examined
- `Canonical Stage`
- `Nature`
- `Ready / Unready / Stayed`
- `Cases` (specifically the case type prefix, e.g., 'R.C.C.')

## B. Distinct values
**Nature**:
```text
nature
NaN                      14
Regular IPC              14
Appln. U/sec. 12         11
Other Summary             7
U/sec. 156_3 Cr.P.C.      6
U/sec. 457 Cr.P.C.        6
U/Sec. 138 N. I. Act      4
Domestic Voilance Act     2
Other Regular             2
U/sec. 125_3 Cr.P.C.      1
Summary IPC               1
```

**Ready / Unready / Stayed**:
```text
ready_unready_stayed
U    39
R    29
```

**Case Prefix**:
```text
case_prefix
R.C.C.          21
PWDVA Appln.    17
Cri.M.A.        16
S.C.C.          14
```

## C. Cross-tabulations
### Nature vs Case Prefix
```text
case_prefix            Cri.M.A.  PWDVA Appln.  R.C.C.  S.C.C.
nature                                                       
Appln. U/sec. 12              0            11       0       0
Domestic Voilance Act         2             0       0       0
NaN                           1             6       5       2
Other Regular                 0             0       2       0
Other Summary                 0             0       0       7
Regular IPC                   0             0      14       0
Summary IPC                   0             0       0       1
U/Sec. 138 N. I. Act          0             0       0       4
U/sec. 125_3 Cr.P.C.          1             0       0       0
U/sec. 156_3 Cr.P.C.          6             0       0       0
U/sec. 457 Cr.P.C.            6             0       0       0
```

## D. Candidate routing signals
1. **Nature vs Case Prefix**: `Nature` contains 14 empty (`NaN`) values. Therefore, `Nature` is **NOT sufficient** to distinguish the case type reliably.
2. **Case Prefix**: The prefix extracted from the `Cases` column (e.g., `Cri.M.A.`, `PWDVA Appln.`, `R.C.C.`, `S.C.C.`) aligns perfectly with the four Unready board sections (`M.A.`, `D.V.`, `R.C.C.`, `S.C.C.`). Every single case has a valid prefix.
3. **Ready / Unready / Stayed**: This field correlates strongly with whether a stage is placed on the READY side (e.g., `Hearing`) or the UNREADY side (e.g., `M.A.`, `D.V.`). For example, `Dismissal Order` exists in both `Hearing` and `M.A.`, meaning the `Ready / Unready` flag is required to disambiguate the side.

## E. Strongly supported routing relationships
1. **Unready Stages**: When `Ready / Unready / Stayed` is 'Unready', cases are distributed to `M.A.`, `D.V.`, `R.C.C.`, or `S.C.C.` based entirely on the **Case Prefix**.
2. **Ready Stages**: Stages inherently linked to trial (e.g., `Evidence Part Heard`, `Arguments`, `Statement U/sec.313 Cr.P.C.`) go to their explicit sections (`Part Heard`, `Argument`, `313`).
3. **Warrants**: `N.B.W._Ready` goes to `Hearing`, while `N.B.W._Unready` goes to `N.B.W. / B.W.` section.

## F. Ambiguous cases
No observed case in the sample is ambiguous if we use `Canonical Stage` + `Ready / Unready / Stayed` + `Case Prefix`.

## G. Information that is still missing
The court officer must explicitly approve the business rule mapping that: `Cri.M.A.` maps to `M.A.`, `PWDVA Appln.` maps to `D.V.`, etc. We cannot assume this legally without their configuration.

## Proposed Routing Decision Table
| Canonical Stage | Additional Field | Value | Candidate Board Section | Confidence | Status |
|---|---|---|---|---|---|
| Evidence Part Heard | None | N/A | Part Heard | High | STRONGLY_SUPPORTED |
| Statement U/sec.313 Cr.P.C. | None | N/A | 313 | High | STRONGLY_SUPPORTED |
| Arguments | None | N/A | Argument | High | STRONGLY_SUPPORTED |
| Judgement | None | N/A | Judgement | High | STRONGLY_SUPPORTED |
| N.B.W._Ready | None | N/A | Hearing | High | STRONGLY_SUPPORTED |
| N.B.W._Unready | None | N/A | N.B.W. / B.W. | High | STRONGLY_SUPPORTED |
| B.W._Ready | None | N/A | Hearing | High | STRONGLY_SUPPORTED |
| B.W._Unready | None | N/A | N.B.W. / B.W. | High | STRONGLY_SUPPORTED |
| Dismissal Order | Ready/Unready | Ready | Hearing | High | STRONGLY_SUPPORTED |
| Dismissal Order | Case Prefix | Cri.M.A. (Unready) | M.A. | High | STRONGLY_SUPPORTED |
| Dismissal Order | Case Prefix | PWDVA Appln. (Unready) | D.V. | High | STRONGLY_SUPPORTED |
| Dismissal Order | Case Prefix | R.C.C. (Unready) | R.C.C. | High | STRONGLY_SUPPORTED |
| Dismissal Order | Case Prefix | S.C.C. (Unready) | S.C.C. | High | STRONGLY_SUPPORTED |
| Steps | Case Prefix | Cri.M.A. | M.A. | High | STRONGLY_SUPPORTED |
| Steps | Case Prefix | PWDVA Appln. | D.V. | High | STRONGLY_SUPPORTED |
| Steps | Case Prefix | R.C.C. | R.C.C. | High | STRONGLY_SUPPORTED |
| Steps | Case Prefix | S.C.C. | S.C.C. | High | STRONGLY_SUPPORTED |