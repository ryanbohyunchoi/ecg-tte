# Remembered user direction: start with the largest exploratory cohort

User direction: "Lets try the largest cohort first and then continue with the
analyses." This selects the broadest reported non-tied candidate population:
**prior general HF I50 evidence OR latest strictly prior numeric EF >1 and <40
within 365 days, without diastolic/HFpEF exclusions**, using the DX_DATE view for
this first exploratory materialization. It does not select the 6,530-person
exclusion variant. Do not silently reinstate those exclusions in this analysis.

Reviewed expected counts: 4,454 carvedilol + 2,922 metoprolol tartrate = **7,376**.
Unresolved competing-arm ties remain outside these two-arm counts. Candidate
anchors, code/date semantics, EF scale/availability and identity remain provisional.
This is a COMET-inspired broad HF/low-EF population, not confirmed HFrEF, a strict
COMET replication, or a finalized new-user cohort. Choosing the first exploratory
population does not freeze an endpoint, causal estimand, PSM or MI model.

Remember alternative sensitivities on the same anchors (DX_DATE, no arm ties):
systolic/combined code OR EF<40 3,971; general HF OR EF<40 with isolated-diastolic/
HFpEF whole-patient exclusion 6,663; any-diastolic/HFpEF whole-patient exclusion
6,530; corresponding code-branch exclusions 6,724 and 6,634. Keep these definitions
available; do not select among them later based on favorable treatment effects.

## Continue now: materialize and audit baseline prescribing history

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
COMET_BROAD_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-broad-XXXXXXXX)
echo "Report: $COMET_BROAD_RUN/report/summary.json"
PYTHONDONTWRITEBYTECODE=1 python scripts/audit_comet_broad_cohort.py \
  --candidate-report /mnt/raid0/rbc58/ecg-tte/audits/comet-candidates-c2FSBqdW/report \
  --output-dir "$COMET_BROAD_RUN/report"
cat "$COMET_BROAD_RUN/report/summary.json"
```

This reads the saved candidate file and small core echo table, without scanning
medications/DX again or using the damaged lab source. It writes restricted
`restricted_broad_candidates.parquet` plus a manifest and aggregate summary to a
fresh RAID directory; no existing output is changed. Its clinical criterion and
input/output hashes are recorded. Shared-reader metadata/footers and candidate
hash are checked; input echo parts receive size/mtime checks, not full rehashing.
Read-only complete snapshots remain mandatory. No automatic resume is offered.

Expected selected counts should reproduce 7,376 before any history exclusions.
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
