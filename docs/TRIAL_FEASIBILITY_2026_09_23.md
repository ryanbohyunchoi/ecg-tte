# Trial feasibility screen (2026-09-23)

Aggregate-only screen to help pick about 10 cardiovascular RCTs for
active-comparator target-trial emulation with ECG embeddings. Screening only:
these are not cohort definitions and not effect estimates.

- Script: `scripts/screen_trial_feasibility.py` (DuckDB over OMOP gold parquet)
- Outputs (restricted, umask 077): `/mnt/raid0/rbc58/ecg-tte/audits/claude-trial-feasibility/feasibility.csv`
  (per arm plus pooled row, with attrition) and `feasibility_ranked.csv`
- Run:
  ```
  python scripts/screen_trial_feasibility.py --omop-dir /mnt/raid0/rbc58/omop/gold \
    --ecg-metadata /mnt/raid0/rbc58/mm_vhd/metadata/ecg_metadata.parquet \
    --echo-metadata /mnt/raid0/rbc58/mm_vhd/metadata/echo_accession_number.parquet \
    --out-csv /mnt/raid0/rbc58/ecg-tte/audits/claude-trial-feasibility/feasibility.csv
  ```

## Definitions

- **Arm drug**: case-insensitive match on `drug_source_value`, split into tokens on `-`,
  compared against ingredient and brand keywords (taken from archived legacy configs,
  plus a few brands found in the data, e.g. Coreg, Toprol, Synjardy, Xultophy). IV
  enalaprilat is excluded from PARADIGM's ACEi arm.
- **New user**: first-ever order of the arm drug with index between 2013-01-01 and
  2024-06-30. No order of the comparator drug in [index-365, index]. Age >= 18. Earliest
  visit_occurrence <= index-365. A person eligible for both arms is kept only at their
  earlier index.
- **Disease gate** (ICD-10 prefix, any time on or before index): HF = I50; AF = I48;
  T2D = E11. ASCVD = I20-I25, I63, I65, I66, I70, I73.9, Z95.1, Z95.5, Z98.61.
  ACS = I21/I24 in [index-30, index]. Gates by trial: EMPA-REG and TECOS = T2D+ASCVD;
  LEADER = T2D+(ASCVD or HF or CKD N18); ONTARGET = ASCVD or T2D.
  DECLARE, CANVAS, CAROLINA and SAVOR = T2D only.
- **ECG / echo**: MRN matched on digits only, with leading zeros stripped. ECG in
  [index-365, index] and [index-90, index]. The CSV also has a 90-day version that
  excludes the index day. Echo = EF between 5 and 90 in [index-365, index].
- **Deaths**: all-cause death in (index, index+1095 days]. **Pooled across arms only.**
  No hazard ratios and no by-arm rates.
- Counts from 1 to 10 are suppressed.

## Ranked results

Ranking criteria:
1. The smaller arm has a final n of at least 300.
2. The pooled final cohort has at least 70% with an ECG in the 90 days before index.
3. A published HR exists.

Ties are broken by whether every arm reaches 70% ECG coverage, then by pooled ECG coverage.

In the table, "ECG ≤90d" and "Echo EF ≤365d" mean an ECG or echo EF in the 90 or 365 days before index.

| Rank | Trial | RCT control | Published HR | Min-arm n | Pooled n | ECG ≤90d pooled (min arm) | Echo EF ≤365d | 3-y deaths (pooled) | Criteria met |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PLATO | active | 0.84 | 3553 | 7871 | 0.825 (0.757) | 0.497 | 1127 | 3/3 |
| 2 | TRITON-TIMI38 | active | 0.81 | 392 | 5060 | 0.784 (0.684) | 0.546 | 811 | 3/3 |
| 3 | COMET | active | 0.83 | 5507 | 18171 | 0.716 (0.668) | 0.503 | 4358 | 3/3 |
| 4 | PARADIGM-HF | active | 0.80 | 3785 | 10580 | 0.670 (0.657) | 0.520 | 2153 | 2/3 |
| 5 | ARISTOTLE | active | 0.79 | 5904 | 28736 | 0.639 (0.568) | 0.416 | 4890 | 2/3 |
| 6 | ROCKET-AF | active | 0.79 | 6212 | 13300 | 0.572 (0.562) | 0.305 | 2041 | 2/3 |
| 7 | RE-LY | active | 0.66 | 1640 | 8227 | 0.572 (0.502) | 0.272 | 1421 | 2/3 |
| 8 | EMPA-REG | placebo | 0.86 | 4432 | 10658 | 0.400 (0.361) | 0.279 | 1241 | 2/3 |
| 9 | TECOS | placebo | 0.98 | 3387 | 6931 | 0.399 (0.391) | 0.201 | 870 | 2/3 |
| 10 | LEADER | placebo | 0.87 | 1420 | 9401 | 0.393 (0.284) | 0.215 | 1148 | 2/3 |
| 11 | CAROLINA | active | 0.98 | 4790 | 11679 | 0.373 (0.266) | 0.182 | 1311 | 2/3 |
| 12 | DECLARE-TIMI58 | placebo | 0.83 | 5622 | 21450 | 0.340 (0.301) | 0.207 | 1975 | 2/3 |
| 13 | CANVAS | placebo | 0.86 | 1878 | 17757 | 0.290 (0.175) | 0.128 | 1430 | 2/3 |
| 14 | SAVOR-TIMI53 | placebo | 1.00 | 751 | 12096 | 0.284 (0.236) | 0.105 | 997 | 2/3 |
| 15 | ONTARGET | active | 1.01 | 945 | 2118 | 0.257 (0.243) | 0.121 | 140 | 2/3 |

What the table shows:
- Every trial passes the sample-size criterion.
- ECG coverage in the 90 days before index is what separates the trials. Only the ACS
  and HF trials reach 70%.
- In the T2D trials, ECG coverage is low (29-40%) and echo coverage is sparse.

## Caveats

- **Orders, not dispensing.** OMOP gold `drug_exposure` is built from orders.
  - Every row has type concept 32817 (EHR).
  - Inpatient administrations are included.
  - Neither the "first-ever" order nor persistence has been checked against pharmacy
    fills.
- **Mapping not validated against raw JDAT.** `drug_source_value` holds only the first
  word of the order name, and the metoprolol drug_concept_id is ingredient-level.
  Because of this, several trial features cannot be applied:
  - metoprolol tartrate vs succinate (COMET)
  - dose (for example, dabigatran 150 mg)
  - enalapril-only ACEi (PARADIGM)
- **Protocol criteria are only partly applied.** The screen uses disease gates only.
  - The HF trials' LVEF criteria are not applied.
  - The PCI requirement (TRITON) is not applied.
  - The ACS arms include clopidogrel users with a recent MI code, whatever their
    indication.
- **Placebo-controlled RCTs.** EMPA-REG, DECLARE, CANVAS, LEADER, TECOS and SAVOR were
  placebo-controlled. For these, DPP4i or sulfonylurea serve as active-comparator
  proxies (RCT-DUPLICATE style), so the published HR is only an indirect benchmark.
  TRANSCEND is placebo-controlled and was not screened separately.
- **Prior-activity requirement.** Requiring a visit 365 days or more before index removes
  about 20-65% of first-time users, depending on the arm. Many are new to the system.
- **ICD-10 only.** Codes are matched on `condition_source_value`, and pre-10/2015 ICD-9
  history may be missing.
- **ECG and echo coverage.**
  - ECG volume dips in 2021.
  - Echo data covers only 2015-07 to 2025-02, which understates echo coverage for
    earlier index dates.
  - The ECG window includes the index day. The same-day share is large: without the
    index day, pooled ECG coverage in the 90 days before index drops by about 0.1-0.3.
    See `frac_ecg_90d_excl_index_day` in the CSV.
- **Death data.**
  - Death capture appears to end around 2024-12, so 3-year windows are incomplete for
    later index dates. See `n_pooled_full_3y_window` in the CSV.
  - The death table carries no cause of death.
  - A small number of deaths are dated on or before index, which is a data-quality flag.
- **Screening only.** All counts are for screening, not definitive cohort sizes.
