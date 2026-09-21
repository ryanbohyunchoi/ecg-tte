# Current user-selected exploratory cohort: HF OR low EF, with exclusions

This supersedes the earlier mistaken interpretation of "largest cohort." The user
explicitly selected the first clarified rule:

**(Prior general HF code OR latest strictly prior EF <40) AND no strictly prior
diastolic/HFpEF exclusion evidence.**

The exclusion applies to the entire patient, including someone with low EF. Use
the existing DX_DATE view and any-diastolic definition, which includes isolated
and combined systolic/diastolic codes and lexical DX_NAME mentions. Same-day and
future diagnoses do not exclude. This is exactly the audited
`general_exclude_any_diastolic_or_hfpef_entire_patient` scenario.

Expected candidates: **4,017 carvedilol + 2,513 metoprolol tartrate = 6,530**.
Before exclusions: 4,454/2,922; expected removed: 437/409 (846 total). Arm ties stay
separate. EF uses numeric >1 and <40, latest prior within365 days, no older fallback;
units and source availability remain unvalidated. This retains the OR pathway,
not HF AND low EF. It is exploratory, not validated HFrEF or a final new-user cohort.

Keep the former 7,376 no-exclusion population and other counted variants as named
sensitivity analyses only. Do not choose among them based on favorable effects.
Version1 broad materialization is superseded; do not reuse it as the selected cohort.
Version2 adds the whole-patient exclusion and records before/after accounting.
Lexical name exclusions are not negation-aware and may overexclude; review this
limitation before freezing a clinical phenotype or statistical protocol.

## Continue now: materialize and audit baseline prescribing history

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
COMET_BROAD_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-broad-excluded-XXXXXXXX)
echo "Report: $COMET_BROAD_RUN/report/summary.json"
PYTHONDONTWRITEBYTECODE=1 python scripts/audit_comet_broad_cohort.py \
  --candidate-report /mnt/raid0/rbc58/ecg-tte/audits/comet-candidates-c2FSBqdW/report \
  --output-dir "$COMET_BROAD_RUN/report"
cat "$COMET_BROAD_RUN/report/summary.json"
```

This reads the saved candidate file, core echo table and projected diagnosis
code/name/date fields to apply the exclusions. It does not scan medications or use
the damaged lab source. It writes restricted
`restricted_broad_candidates.parquet` plus a manifest and aggregate summary to a
fresh RAID directory; no existing output is changed. Its clinical criterion and
input/output hashes are recorded. Shared-reader metadata/footers and candidate
hash are checked; input echo/diagnosis parts receive size/mtime checks, not full rehashing.
Read-only complete snapshots remain mandatory. No automatic resume is offered.

Expected selected counts should reproduce 6,530 before any history exclusions.
If they differ, reconcile inputs/rules before using the result. The audit reports
mutually exclusive combinations of prior365-day family orders and undated family
orders, by arm and calendar year, plus code-only/EF-only/both evidence groups.
Neither missing prior orders nor absence of undated orders proves incident use or
complete observation. This history covers carvedilol/metoprolol families only,
not every beta-blocker, and is not dispensing/adherence. No history exclusion is
applied now. Candidate dates and any future/same-day QC flags retained from the
upstream roster are not all baseline modeling features; they require the separate
feature dictionary and pre-index availability rules before PSM.

Return reviewed summary.json only. Patient files remain on H100. Next use these
counts to resolve new-prescribing/observation and calendar overlap, then extract
validated covariates and assess missingness before imputation/matching. Broad
population choice does not remove mandatory source, endpoint or timing gates.
