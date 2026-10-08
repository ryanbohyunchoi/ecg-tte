# Version 1 audit (2026-10-08)

Independent audit of version 1 (tag `trace-v1`, 5c98301), after the user chose to revert from R2 to version 1. R2 and the LEGEND-style analysis are preserved on branch `r2`. Three agents ran independently: none read the others' reports, and none edited version 1 files.

| Report | Scope |
|---|---|
| [DEFECT_IMPACT.md](DEFECT_IMPACT.md) | Effect of each of the 9 known version 1 defects on each paper2 headline claim, rerun with the defect corrected |
| [CLAIMS_RECHECK.md](CLAIMS_RECHECK.md) | 160 claims in paper2.md and the figure legends, recomputed from cell-level outputs with independent code |
| [CODE_PRIVACY_REVIEW.md](CODE_PRIVACY_REVIEW.md) | Correctness review of the paper2 pipeline; privacy scan of tracked files |

Code: `scripts/v1_audit/`. Aggregate outputs: `/mnt/raid0/rbc58/ecg-tte/audits/claude-v1-audit/` (restricted per-trial files stay on raid0).

## Bottom line

- **Primary claims hold.** PS-CVD5 + ECG 8.8% (4.4–13.3), + CLMBR-T 12.4%, + both 13.5%. They reproduce exactly from cells, are unchanged by leakage masking, and survive Benjamini–Yekutieli. The results-blind 35-trial set gives 8.6 / 12.0 / 12.8%.
- **ECG robustness caveats.**
  - Excluding index-day ECGs gives 6.9% (0.4–13.4).
  - A cross-validated PS penalty gives 5.7% (−0.5 to 11.4).
  - Against the permuted ECG under CV tuning (R2): 7.9%.
- **Conclusion changes.**
  1. CLMBR-T vs PS-Clinical narrows from −4.9% to −2.6% once near-duplicates (echo EF, LV systolic grade, eGFR) are masked.
  2. The CLMBR-T loss under IPTW is weight instability; trials with ESS ≥ 0.5 give 7.9%.
  3. Agreement by quality tier reverses under the blind tiers.
- **Code.** No blocking bug. One should-fix: PROTECT AF hdPS200 cells with 1–10 matched pairs still enter the balance contrasts (`scripts/v21/paper2_grid.py` `load_F`); treating them as failed changes some hdPS contrasts. Undisclosed: index-day ECGs, and that plasmode bias removal is null-corrected.
- **Text.** All numbers in paper2.md are correct. 23 of 160 claims need wording, scope or methods fixes (CLAIMS_RECHECK.md).
- **Privacy.** paper2 and its figures are clean. Small counts (1–10) exist in older tracked docs that are already on `origin`: `docs/COMET_OUTCOMES_HANDOFF.md`, `docs/DECISIONS.md`, `docs/HANDOFF_HISTORY.md`, `tasks/todo.md` and others; see CODE_PRIVACY_REVIEW.md. `.gitignore` does not exclude `*.docx` or `audits/`.
