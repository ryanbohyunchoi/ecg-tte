# Fresh COMET MEDS and frozen CLMBR

Implemented stages: build_comet_meds.py and encode_comet_clmbr.py. Local synthetic
verification is not H100 validation. No patient processing or GPU inference was
performed by the assistant. Archived modules are not imported.

## 1. Build once from existing gold

Use the Python environment that ran the input coverage check (pyarrow required).
This consumes existing OMOP, not raw JDAT or the old cohort-scoped MEDS cache.
Required domains: conditions, drugs, procedures, measurements (labs/vitals), visits.
The builder validates required columns/types and stops if a domain is missing.
It projects cohort rows, stages privately on RAID with SQLite, maps only relevant
concepts, and emits sorted subject-disjoint Parquet shards. Gold tables are not
modified. All original candidate patients stay in the restricted roster and
coverage denominators even if they cannot later be encoded.

```bash
(
set -e
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/shared
COMET_MEDS_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/shared/comet-meds-v1-XXXXXXXX)
echo "MEDS output: $COMET_MEDS_RUN/meds"
python scripts/build_comet_meds.py \
  --source-report /mnt/raid0/rbc58/ecg-tte/audits/comet-mice-prep-M9F28Lk2/report \
  --gold-root /mnt/raid0/rbc58/omop/gold \
  --concept /mnt/raid0/rbc58/mosaic/mapping/CONCEPT.csv \
  --output-dir "$COMET_MEDS_RUN/meds" || {
    cat "$COMET_MEDS_RUN/meds/summary.json"
    exit 1
  }
cat "$COMET_MEDS_RUN/meds/summary.json"
)
```

Save the printed MEDS path; the variable inside the parentheses does not persist.
A completed build can be reused for different encoder runs without rescanning gold.
New runs refuse existing destinations. Partial builds cannot be reused as complete;
failed SQLite staging remains available for local diagnosis.

### Declared MEDS v1 contract

All available clinical history strictly before index-date midnight. Date columns
are a fallback only when the preferred datetime is absent/null; invalid nonnull
datetimes are not silently replaced. Offset-bearing/missing times are excluded
with counts. Birth requires a consistent exact birth_datetime; no inferred
January 1 birthdays. Events before known birth are excluded and counted. Missing
birth prevents encoding, not inclusion in the cohort coverage report.

Concepts resolve through the specified vocabulary snapshot; only visit IDs
9201/9202/9203 have explicit Visit/IP, Visit/OP, Visit/ER overrides. Unmapped
concepts/rows are counted. Duplicate source events are preserved; pinned FEMR
performs its own documented same-day feature deduplication. Source availability
at index is not established by event timestamps alone.

Core flat fields: subject_id int64, time timestamp[us], code string,
numeric_value float32, with unit/source_domain/source_concept_id extras.
The flat artifact is translated to FEMR's pinned nested patient API at inference.
Birth is stored as MEDS_BIRTH and converted explicitly to MEDS 0.1.3's birth code.
This is a versioned adapter contract, not a universal MEDS-version compatibility
claim. Numeric values/units are observed; no MICE values or unit conversion.
Overflow/nonfinite/unparseable numerical values become null with counts.
No static sex/race tokens, drug dose/adherence, observation-table events or endpoints
are added in this initial five-domain contract. Sex is retained in the roster.
Any later addition must be a new declared representation specification.

Partition provenance uses source size/mtime plus concept and baseline SHA256;
this avoids an extra read of the full gold. Generated MEDS outputs are SHA256
verified before encoding. Source semantic/clinical validation remains separate.

## 2. Run a 32-patient encoder smoke test

Use an existing compatible GPU environment, not the R/MICE environment. Required
adapter versions: femr==0.2.3, meds==0.1.3; also pyarrow, numpy, datasets,
transformers, CUDA torch and a compatible xformers build. No automatic environment
modification, model download or CUDA repair is performed. The runner reports
missing packages and stops; actual binary compatibility is tested on H100.
The verified wheel source uses convert_patient/get_feature_codes and a local
nonhierarchical tokenizer. A hierarchical tokenizer requires an explicit ontology
contract and is rejected in v1. The local model must have 768 output dimensions
and load without missing/unexpected/mismatched state keys. File hashes define the
actual weights used; directory name alone is not model provenance validation.

Set COMET_MEDS_ROOT to the printed absolute path from stage 1, then run:

```bash
(
set -e
cd "$HOME/github/ecg-tte"
umask 077
: "${COMET_MEDS_ROOT:?Set this to the completed MEDS output path}"
CLMBR_ENCODE_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-clmbr-smoke-XXXXXXXX)
echo "Encoder report: $CLMBR_ENCODE_RUN/report"
python scripts/encode_comet_clmbr.py \
  --meds-root "$COMET_MEDS_ROOT" \
  --model-root /mnt/raid0/eo287/clmbr \
  --numeric-mode native \
  --max-tokens 4096 --limit 32 \
  --output-dir "$CLMBR_ENCODE_RUN/report" || {
    cat "$CLMBR_ENCODE_RUN/report/summary.json"
    exit 1
  }
cat "$CLMBR_ENCODE_RUN/report/summary.json"
)
```

Native passes numeric values and raw units to the pinned tokenizer. Tokenizer
acceptance is counted by arm; valid mapping does not guarantee accepted tokens or
valid clinical units. --numeric-mode code-only is a distinct explicitly labeled
sensitivity run, not automatic fallback when native acceptance is poor.

Inference freezes all weights, uses eval/inference mode and returns the last
retained token's raw 768D vector. The latest 4096 token positions are retained
AFTER full-history tokenization; truncation counts are reported. Age anchors come
from exact birth in the full patient history. Smoke targets are deterministic,
arm-balanced by subject ID and not claimed representative. Source cutoffs and
returned patient IDs/timestamps are checked; there is no future-vector fallback.
Missing birth/history or zero accepted clinical events are recorded per patient;
unexpected runtime/model failures stop the run. No patient-level values are printed.

After reviewing successful smoke coverage, numerical validity and checkpoint
identity, rerun the same command in a fresh output directory with --limit 0 for
the full cohort. The completed MEDS remains unchanged. No PSM tuning or matching
runs here. Full inference outputs raw vectors, restricted patient statuses and
hashed manifests; partial inference outputs are not automatically resumable or
approved caches. No assertion of better balance is made.

Before direct-distance matching, freeze normalization/matching settings and use
identical clinical evaluation variables and common-population denominators.


## Observed Mosaic runtime issue (2026-09-23)

The first import test found FEMR0.2.3/MEDS0.1.3 but SciPy HiGHS loaded the system
libstdc++.so.6 without CXXABI_1.3.15. The sibling Mosaic handoff records success
using the C++ runtime from Python's sys.prefix; CONDA_PREFIX had pointed elsewhere.
For this specific error, run a fresh process using the explicit mosaic interpreter
and LD_PRELOAD set to Path(sys.prefix)/lib/libstdc++.so.6. Scope that override to
the launch subshell, never a permanent shell startup change. Verify scipy.optimize,
FEMR imports and CUDA before smoke. Do not claim this current environment repaired
until that preflight succeeds; newer torch/transformers compatibility remains a
separate runtime question. No package reinstall or MEDS rebuild is indicated yet.


## Model configuration defaults

The loader resolves config.json using FEMRModelConfig before checking hidden_size.
Default values may be omitted from serialized JSON; the summary records raw and
resolved values and identifies defaulted fields. Explicit incompatible dimensions
are not overridden. The identical resolved config is used for strict weight loading;
returned representation shape must still be768. This fixes the raw-JSON rejection
seen in comet-clmbr-smoke-dS7xNUcE, not a verified H100 inference success.
