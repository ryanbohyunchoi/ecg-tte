# Expanded COMET beta-blocker history review

This audit uses the completed selected v2 cohort: (general HF code OR latest prior EF <40) AND no prior diastolic/HFpEF evidence. The reviewed cohort contains 6,530 candidate keys (4,017 carvedilol; 2,513 metoprolol tartrate). It preserves the roster and index dates. It does not create an eligible new-user cohort or run matching.

The existing history covered carvedilol/metoprolol families. This screen adds named generic leads from the WHO ATC [C07AA](https://atcddd.fhi.no/atc_ddd_index/?code=C07AA&showdescription=yes), [C07AB](https://atcddd.fhi.no/atc_ddd_index/?code=C07AB&showdescription=yes), and [C07AG](https://atcddd.fhi.no/atc_ddd_index/?code=C07AG&showdescription=yes) lists, checked 2026-09-21. Brand-only names and other words ending in “olol” are unresolved review leads. This is not exhaustive historical vocabulary or an approved medication-ID mapping. All routes and order classes are retained for review, including ophthalmic and intravenous records; a match alone does not exclude a patient.

Run on H100, with the repository's PyArrow environment:

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
COMET_BETA_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-beta-history-XXXXXXXX)
PYTHONDONTWRITEBYTECODE=1 python scripts/audit_comet_beta_history.py \
  --audit-root /mnt/raid0/rbc58/ecg-tte/audits \
  --output-dir "$COMET_BETA_RUN/report"
cat "$COMET_BETA_RUN/report/summary.json"
```

Discovery requires exactly one verified v2 report beneath a `comet-broad-*` run directory. If multiple exist, use `--cohort-report` with the intended absolute report directory instead of `--audit-root`; do not automatically pick the newest. Each output directory must be new. No labs are read or rebuilt.

## Review outputs

- `summary.json`: mutually exclusive patient groups by arm, prior days 1–365 generic leads, undated generic leads, unresolved prior/undated leads and other same-day leads. These are lexical evidence counts, not class washout or eligible N. Future and older non-index orders do not contribute. Index orders are verified against original medication source-row lineage and kept separate.
- `restricted_medication_mapping.json`: medication names, IDs, routes and order classes with record counts. Keep this on H100 for local review; unexpected text may contain sensitive information. Do not paste the entire catalog.

The script verifies the selected cohort hash/row count and core manifest, requires a complete shared medication table, checks index lineage, and rejects missing lineage, oversized fields or catalog overflow. No raw rows are skipped or source files changed. Runtime has not been measured on H100; it scans projected columns from 30.9 million medication rows, so allow several minutes.

## What follows

Review medication-ID/formulation/route mappings and baseline observation coverage before freezing a 365-day class-wide washout rule. Assess inclusion/exclusion requirements at the qualifying prescription date, with baseline features strictly before it. A first observed prescription is not proof of first use. Do not move an index to a later refill simply because eligibility becomes satisfied later. Unsupported mandatory criteria must stop clinical eligibility; adaptations must be explicit. No future visit or refill requirement is introduced.

Synthetic verification covers time boundaries, combination/brand/topical leads, preserved indices, group denominators, source hash changes, missing index lineage and output non-overwrite. Clinical semantics and actual cluster results remain unverified.
