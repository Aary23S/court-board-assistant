# Routing Exceptions

## Status

15 unresolved cases from reference sample (68 total).

## Exception Group 1 — N.B.W._Unready

**Affected Stages:** `N.B.W._Unready`, `B.W._Unready`

**Affected Prefixes:** `R.C.C.`, `S.C.C.`, `Cri.M.A.`, `PWDVA Appln.`

**Current Confirmed Rules:** 
- The source `Ready / Unready` status determines the board side.
- For Unready cases, the case prefix determines the final board section (e.g., `R.C.C.` prefix → `R.C.C.` section).

**Current Template Structure:** 
- The stage `N.B.W._Unready` exists *only* under the `N.B.W. / B.W.` section. It does *not* exist in the `R.C.C.`, `S.C.C.`, `M.A.`, or `D.V.` sections.

**Contradiction:** 
When a case like `R.C.C./300258/1996` with stage `N.B.W._Unready` and status `Unready` is processed, the rule routes it to the `R.C.C.` section. However, the template rejects it because the `N.B.W._Unready` row does not exist in the `R.C.C.` section.

**Exact Officer Question:**
"For an Unready case whose Next Purpose/Canonical Stage is N.B.W._Unready or B.W._Unready, should it always go to the N.B.W. / B.W. section regardless of case prefix, or should the case prefix rule continue to determine the section?"

---

## Exception Group 2 — Ready + Unready-only Stage

**Affected Stages:** `Steps`, `Reply/Say` (and potentially others)

**Current Template Structure:** 
- `Steps` and `Reply/Say` exist as rows under the Unready-side sections (`M.A.`, `D.V.`, `R.C.C.`, `S.C.C.`).
- They do *not* exist as rows under the Ready-side sections (`Hearing`, `Part Heard`, `313`, `Argument`, `Judgement`).

**Contradiction:**
When a case like `S.C.C./2057/2017` has stage `Steps` and status `Ready`, the confirmed rule dictates it must go to the Ready side. The engine searches all Ready-side sections for a `Steps` row but finds 0 matching rows. The case cannot be routed.

**Exact Officer Question:**
"If a case is marked Ready but its Next Purpose corresponds to a stage that appears only in the Unready sections of the final board (for example Steps or Reply/Say), where should that case be listed?"
- A. It should go to a specific existing Ready-side row.
- B. It should still appear in the relevant Unready section despite the Ready flag.
- C. A new Ready-side row should be added.
- D. Another rule applies.

---

## Officer Decisions Required

1. **For an Unready case whose Next Purpose/Canonical Stage is N.B.W._Unready or B.W._Unready, should it always go to the N.B.W. / B.W. section regardless of case prefix, or should the case prefix rule continue to determine the section?**

2. **If a case is marked Ready but its Next Purpose corresponds to a stage that appears only in the Unready sections of the final board (for example Steps or Reply/Say), where should that case be listed? (A) A specific existing Ready-side row, (B) The relevant Unready section despite the Ready flag, (C) A new Ready-side row, or (D) Another rule applies?**
