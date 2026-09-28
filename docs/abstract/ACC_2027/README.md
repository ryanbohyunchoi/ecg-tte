# ACC abstract

## Files
- `ACC_ABSTRACT.md` = `ACC_ABSTRACT_v4.md`: **current draft (2026-09-28)**, PI-preferred structure. It is 1,293 characters excluding spaces and title, uses all 38 trials and contains no AF claim.
  - Balance 51 → 57%, 28/38, p = 0.0002, cluster p = 0.017: `claude-v18-embed-compare/summary.csv` (all38, P1, ECG vs base, lt01).
  - Gap 0.26 → 0.21, 25/38, p = 0.002; benchmark shuffle p = 0.22, hence 'attenuating'.
  - Simulation (NT-proBNP 21%, placebo ~0): `docs/v19/G2_SIMULATION.md`, as-designed scenario.
- `ACC_ABSTRACT_v3_audit.md`: **recommended current draft**, from the round-4 audit (docs/v18/AUDIT_ROUND4.md §7). It is 1,287 characters excluding spaces, labels and title.
- `ACC_ABSTRACT_v2_superseded.md`: the v2 draft (2026-09-27). **Do not submit as is.**
  - Its AF sentence is post hoc, and the AF signal failed prespecified confirmation (3/5, p = 0.19).
  - Its "agreement with RCTs" claim is generic shrinkage.
  - "Absent from structured data" is contradicted by CLMBR.
- Figure: pending.

## Where each number comes from
| Claim | Source |
|---|---|
| 38 trials: 18 v1.6 (hypothesis-generating) + 15 v1.7 + 5 v1.8 AF | `docs/v16/V17_CONFIRMATION_PLAN.md`, `docs/v17/candidates.md`, `docs/v18/af_candidates.md` |
| Balance 53% → 59%, 25/33, p < 0.001 | `docs/v17/V17_CONFIRMATION_RESULTS.md` (all33, P1; 18 of these 33 are the discovery trials) |
| Confirmation 52% → 58%, p = 0.03; cluster p 0.078; P2 p 0.17 | same file (new15) |
| \|Δlog HR\| 0.26 → 0.21, p = 0.004; new15 p = 0.074; shuffle p = 0.37 | same file |
| AF did not replicate (3/5, p = 0.19) | `docs/v18/AF_CONFIRMATION_RESULTS.md` |
| The structured-EHR embedding (CLMBR) matched the ECG | `docs/v18/CLMBR_RESULTS.md` |

## Caveats
1. Outside AF, the reduction in \|Δ\| is generic shrinkage toward typical RCT effects; the benchmark shuffle fails.
2. **The AF category is post hoc and failed prespecified confirmation.**
3. "Placebo had no effect" refers to balance only.
4. The audits are in `docs/v16/AUDIT_V16*.md` and `docs/v18/AUDIT_ROUND4.md`. The closest precedent is DISCO (Biswas … Khera, EHJ 2025 suppl). The framing model is German et al., Nat Genet 2025.
