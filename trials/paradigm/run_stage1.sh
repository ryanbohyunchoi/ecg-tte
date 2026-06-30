#!/usr/bin/env bash
# trials/paradigm/run_stage1.sh — Stage 1 pool builder for PARADIGM-HF
# Run from repo root: bash trials/paradigm/run_stage1.sh

set -euo pipefail

DRUG_DIR="/home/rbc58/mnt/ecg-tte/drugs"
OUT_ROOT="/home/rbc58/mnt/ecg-tte/runs"
OMOP="/mnt/raid0/bb2238/ecg_ascvd/omop_database"
META="/mnt/raid0/rbc58/mm_vhd/metadata"

MERGED_DM="${DRUG_DIR}/home_meds_merged.parquet"

# ── Merge home_meds shards (load_drug_master needs a single parquet file) ──────
if [ ! -f "${MERGED_DM}" ]; then
    echo "[stage1] Merging home_meds shards → ${MERGED_DM}"
    python - <<'PYEOF'
import pandas as pd
from pathlib import Path
import os

drug_dir  = os.environ.get("DRUG_DIR", "/home/rbc58/mnt/ecg-tte/drugs")
out_path  = os.environ.get("MERGED_DM", drug_dir + "/home_meds_merged.parquet")
shards    = sorted(Path(drug_dir).glob("home_meds_*.parquet"))
print(f"  Merging {len(shards)} shards: {[p.name for p in shards]}")
df = pd.concat([pd.read_parquet(p) for p in shards], ignore_index=True)
print(f"  Rows: {len(df):,}   Unique MRNs: {df['MRN'].nunique():,}")
df.to_parquet(out_path, index=False)
print(f"  Written: {out_path}")
PYEOF
else
    echo "[stage1] Using existing ${MERGED_DM}"
fi

export DRUG_DIR MERGED_DM

# ── Stage 1 ────────────────────────────────────────────────────────────────────
# NOTE: visit_occurrence not present in this OMOP extract (not listed in
# /mnt/raid0/bb2238/ecg_ascvd/omop_database/). Omitting --visit-dir; the HF
# hospitalization endpoint will fall back to condition-date only (see proxy_note
# in configs/paradigm_hf.yaml). This overestimates HF-hosp events slightly —
# acceptable for an initial run; revisit if visit_occurrence becomes available.

echo "[stage1] Running stage1_build_pool.py for paradigm_hf ..."
mkdir -p "${OUT_ROOT}"

python scripts/stage1_build_pool.py \
    --config         configs/paradigm_hf.yaml \
    --person-parquet "${OMOP}/person/person.parquet" \
    --condition-dir  "${OMOP}/condition_occurrence" \
    --death-parquet  "${OMOP}/death/death.parquet" \
    --drug-master    "${MERGED_DM}" \
    --echo-meta      "${META}/echo_metadata.parquet" \
    --ecg-meta       "${META}/ecg_metadata.parquet" \
    --output-root    "${OUT_ROOT}" \
    2>&1 | tee "${OUT_ROOT}/paradigm_hf_stage1.log"

echo "[stage1] Done. Outputs in ${OUT_ROOT}/paradigm_hf/"
echo "  Check: ${OUT_ROOT}/paradigm_hf/pool/pool.parquet"
echo "  Log  : ${OUT_ROOT}/paradigm_hf_stage1.log"
