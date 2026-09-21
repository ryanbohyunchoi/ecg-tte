# Adapted COMET eligibility feasibility — core sources

This is the next audit under [the selected adapted protocol](COMET_ADAPTED_PROTOCOL.md). It preserves all 6,530 candidate keys and index dates. It scans complete shared medication, diagnosis and echo tables; the failed extension is not read. It does not construct a clinically eligible cohort or perform PSM.

## Run on H100

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
COMET_ELIG_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-eligibility-XXXXXXXX)
PYTHONDONTWRITEBYTECODE=1 python scripts/audit_comet_eligibility.py \
  --cohort-report /mnt/raid0/rbc58/ecg-tte/audits/comet-broad-excluded-cnG52aaY/report \
  --output-dir "$COMET_ELIG_RUN/report"
cat "$COMET_ELIG_RUN/report/summary.json"
```

All outputs stay under RAID. Use the PyArrow environment used for previous audits. Cluster runtime is unmeasured; allow several minutes for one medication, echo and two diagnosis projection scans. No raw-file rebuild is needed.

## Reading the report

`criterion_register` lists 32 original trial criteria and their current ascertainment limitations, with clinical meets/fails/unknown counts. Clinical status remains unknown in this first pass because the available screens have not been validated as eligibility rules. This is intentional: a proxy or missing record cannot establish clinical eligibility. It is not a claim that all patients are clinically ineligible.

Separate sections quantify what can be observed:

- `numeric_screens`: latest strictly prior echo within365 days, candidate numeric range >1 to100, comparing EF≤35 and EF<40. EF35 is included in the first comparison; EF40 fails the second. Missing, invalid, stale or conflicting latest-day values are unknown; no older-value fallback. Units and report availability remain unvalidated. Failing EF≤35 alone does not fail the original ventricular-function criterion, which had an alternative qualification pathway.
- `beta_lookback_counts`: named generic leads within14,30,90,180,365 days. No named lead is not proof of no treatment. All routes/classes remain included; windows are screens, not selected washout policies.
- `signal_counts`: prior medication-name and diagnosis-code leads, undated beta leads and same-day beta leads. Same-day leads include the index orders and are not prior exposure. ACE inhibitor leads at least28 days before index and diuretic leads at least14 days before index do not establish treatment continuity, stability, qualifying dose or tolerance. Only selected generic names are searched, so absence is not class-wide absence. Alpha names are an incomplete review set and do not substitute for a full alpha-blocker map.
- Recent MI leads use I21/I22; cerebrovascular leads use I60–I64. These are lexical family screens, not validated ICD10-CM/year-specific or incident-event phenotypes. I62 can capture other intracranial hemorrhage. Lists must consist entirely of syntactically valid comma/semicolon/pipe-separated code tokens; malformed or empty/NULL cells are counted separately. No ICD9 interpretation. DX_DATE must be within two calendar months strictly before index, not a 60-day substitution. Undated leads remain separate. No negative disease inference from absent codes.
- `overlapping_evidence_groups`: joint EF≤35 screen, prior365 beta-name lead, recent MI lead and recent cerebrovascular lead. These mutually exclusive combinations reconcile to the roster; they are not a sequential exclusion flowchart.

Medication windows use ORDER_INST calendar days, not dispensing or active-treatment dates. Diagnosis source membership does not establish an inpatient admission. Same-day/future DX and echo values do not inform these screens. Exact patient-key identity and all clinical source semantics still require validation.

`restricted_evidence.parquet` stays on H100. It contains a representative source row and evidence date for each positive signal, plus a representative latest-prior echo row and its screen state. It is not an exhaustive event export; same-day echo disagreement may have additional contributing rows in the source. The manifest records input/output and implementation hashes. Neither this patient-level file nor raw catalogs should be pasted into chat. Return only the reviewed summary.

## Original-to-adapted decisions

The [original design sections 2.1–2.2](https://onlinelibrary.wiley.com/doi/full/10.1016/S1388-9842%2802%2900025-9) are the register's reference. Code-family labels were checked against [CMS code listings](https://www.cms.gov/medicare-coverage-database/view/article.aspx?articleid=56823) and the [CDC ICD10 tabular list](https://www.cdc.gov/nchs/nvss/manuals/2025/2e-vol1-2025.html); these sources do not validate our JDAT phenotypes.

The selected broader HF rule remains in force as the starting population. For other criteria, the adapted decision is pending: require a validated measure, use an explicitly justified proxy, or document omission. This audit does not silently omit a mandatory rule. Numeric or lexical screens are not hard exclusions. No attrition is applied until these decisions and missing-data policies are frozen.

Next review medication-ID/route mappings and choose a source recovery/rebuild path for demographics, encounters and vitals independently of the corrupted lab file. Do not bypass the failed snapshot's completion gate. Age, BP, pulse, clinical stability, dose, laboratory requirements and remaining diagnoses need those sources or mappings before they can be assessed. Missing values do not become normal, and MICE cannot establish eligibility.

Synthetic tests check calendar boundaries, future/same-day separation, latest invalid echo without fallback, dose/continuity uncertainty, denominator reconciliation, immutable roster and rejection of an incomplete core snapshot. Actual H100 results remain pending.
