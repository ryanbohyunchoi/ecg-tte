#!/usr/bin/env bash
# trials/paradigm/run_paradigm_full.sh
# Autonomous end-to-end PARADIGM-HF rebuild + MICE analysis.
#   git pull → detect labs/vitals dirs → stage1 (full features) → stage3
#   → feature inventory → stage4 (MICE m=5, denominator both).
# Skips stage2 (ECG embeddings not needed for PSM/balance).
# NOT set -e: continues past soft failures and logs them. Hard prerequisites
# (stage1/stage3 outputs) abort with a clear STATUS line.
#
# Launch (survives logout):
#   cd ~/github/ecg-tte
#   nohup bash trials/paradigm/run_paradigm_full.sh > /dev/null 2>&1 &
# Check progress any time:
#   cat /home/rbc58/mnt/ecg-tte/runs/paradigm_hf_STATUS.txt

set -uo pipefail

REPO="$HOME/github/ecg-tte"
cd "$REPO" || { echo "no repo at $REPO"; exit 1; }

OUT_ROOT="/home/rbc58/mnt/ecg-tte/runs"
OMOP="/mnt/raid0/bb2238/ecg_ascvd/omop_database"
META="/mnt/raid0/rbc58/mm_vhd/metadata"
DRUG_DIR="/home/rbc58/mnt/ecg-tte/drugs"
MERGED_DM="${DRUG_DIR}/home_meds_merged.parquet"

RUN_NAME="mice_full"                      # new run — does NOT clobber existing 'default'
RUN_DIR="${OUT_ROOT}/paradigm_hf/runs/${RUN_NAME}"
COHORT="${RUN_DIR}/comet_cohort.parquet"
DRUG_POOL="${OUT_ROOT}/paradigm_hf/pool/drug_master_pool.parquet"
TS="$(date +%Y%m%d_%H%M%S)"
LOG="${OUT_ROOT}/paradigm_hf_full_${TS}.log"
STATUS="${OUT_ROOT}/paradigm_hf_STATUS.txt"

mkdir -p "$OUT_ROOT" "$RUN_DIR"
exec > >(tee -a "$LOG") 2>&1             # all stdout+stderr → log (and console)

step(){ echo; echo "=========== [$(date +%H:%M:%S)] $* ==========="; }
note(){ echo "[$(date +%H:%M:%S)] $*" | tee -a "$STATUS"; }

: > "$STATUS"
note "START PARADIGM-HF full rebuild.  run=${RUN_NAME}"
note "full log: ${LOG}"
note "arms: sacubitril_valsartan (treated) vs acei (control)"

# ── 0. pull latest code (bounds fix etc.) ─────────────────────────────────────
step "git pull"
if git pull --ff-only; then note "code @ $(git rev-parse --short HEAD)"
else note "WARN git pull failed — running on $(git rev-parse --short HEAD)"; fi

# ── 1. detect labs/vitals (measurement) + Z-code (observation) dirs ───────────
step "detect measurement / observation dirs"
MEAS_ARG=""; OBS_ARG=""
MEAS_FILE="$(find "$OMOP" -maxdepth 2 -name 'measurement_*.parquet' 2>/dev/null | head -1)"
if [ -n "$MEAS_FILE" ]; then MEAS_ARG="--measurement-dir $(dirname "$MEAS_FILE")"; fi
OBS_FILE="$(find "$OMOP" -maxdepth 2 -name 'observation_icd10_*.parquet' 2>/dev/null | head -1)"
if [ -n "$OBS_FILE" ]; then OBS_ARG="--observation-dir $(dirname "$OBS_FILE")"; fi
note "measurement (labs/vitals): ${MEAS_ARG:-NOT FOUND — labs/vitals skipped}"
note "observation (Z-codes):     ${OBS_ARG:-NOT FOUND — zcodes skipped}"

# ── 2. ensure merged drug_master ──────────────────────────────────────────────
step "ensure merged drug_master"
if [ ! -f "$MERGED_DM" ]; then
  DRUG_DIR="$DRUG_DIR" MERGED_DM="$MERGED_DM" python - <<'PYEOF'
import pandas as pd, os
from pathlib import Path
dd=os.environ["DRUG_DIR"]; out=os.environ["MERGED_DM"]
sh=sorted(Path(dd).glob("home_meds_*.parquet"))
df=pd.concat([pd.read_parquet(p) for p in sh],ignore_index=True)
df.to_parquet(out,index=False); print(f"merged {len(sh)} shards, {len(df):,} rows")
PYEOF
  note "merged drug_master built"
else
  note "using existing merged drug_master"
fi

# ── 3. STAGE 1 — rebuild pool with full feature set ───────────────────────────
step "STAGE 1 — build pool (full features${MEAS_ARG:+ + labs/vitals})"
python scripts/stage1_build_pool.py \
    --config         configs/paradigm_hf.yaml \
    --person-parquet "${OMOP}/person/person.parquet" \
    --condition-dir  "${OMOP}/condition_occurrence" \
    --death-parquet  "${OMOP}/death/death.parquet" \
    --drug-master    "${MERGED_DM}" \
    --echo-meta      "${META}/echo_accession_number.parquet" \
    --ecg-meta       "${META}/ecg_metadata.parquet" \
    --output-root    "${OUT_ROOT}" \
    ${MEAS_ARG} ${OBS_ARG}
RC=$?
if [ "$RC" -eq 0 ] && [ -f "${OUT_ROOT}/paradigm_hf/pool/pool.parquet" ]; then
  note "STAGE1 OK (rc=$RC)"
else
  note "STAGE1 FAILED (rc=$RC) — aborting (see log)"; note "DONE (failed at stage1)"; exit 1
fi

# ── 4. STAGE 3 — filter to analysis cohort ────────────────────────────────────
step "STAGE 3 — filter cohort (run=${RUN_NAME})"
python -u scripts/stage3_filter.py \
    --config           configs/paradigm_hf.yaml \
    --pool-dir         "${OUT_ROOT}/paradigm_hf/pool" \
    --output-dir       "${OUT_ROOT}/paradigm_hf" \
    --run-name         "${RUN_NAME}" \
    --min-fills        2 \
    --persistence-days 180
if [ -f "$COHORT" ]; then note "STAGE3 OK — cohort at $COHORT"
else note "STAGE3 FAILED — no cohort produced — aborting"; note "DONE (failed at stage3)"; exit 1; fi

# ── 5. Feature inventory on the NEW cohort ────────────────────────────────────
step "feature inventory (new cohort)"
python scripts/feature_inventory.py \
    --cohort "$COHORT" \
    --treated-arm sacubitril_valsartan --control-arm acei \
    --out "${RUN_DIR}/feature_inventory.csv"
if [ -f "${RUN_DIR}/feature_inventory.csv" ]; then
  PRESENT=$(python - "$RUN_DIR/feature_inventory.csv" <<'PYEOF'
import pandas as pd,sys
d=pd.read_csv(sys.argv[1]); print(int((d['present']==True).sum()), int(len(d)))
PYEOF
)
  note "feature inventory OK — present/total: ${PRESENT}"
else note "WARN feature inventory did not write CSV"; fi

# ── 6. STAGE 4 — MICE analysis (m=5) + complete-case sensitivity ──────────────
step "STAGE 4 — MICE (m=5), denominator both"
python -u scripts/stage4_analyze.py \
    --cohort           "$COHORT" \
    --output-dir       "$RUN_DIR" \
    --treated-arm      sacubitril_valsartan \
    --control-arm      acei \
    --trial-name       PARADIGM-HF \
    --reference-hr     0.80 \
    --drug-pool        "$DRUG_POOL" \
    --exclude-psm-cols acei_arb \
    --event-col        event_death \
    --time-col         time_to_death \
    --n-imputations    5 \
    --caliper-sd       0.20 \
    --denominator      both
if [ -f "${RUN_DIR}/results_summary.csv" ]; then note "STAGE4 OK"
else note "WARN stage4 produced no results_summary.csv"; fi

# ── 7. Headline summary into STATUS ───────────────────────────────────────────
step "summary"
note "---------- RESULTS SUMMARY ----------"
if [ -f "${RUN_DIR}/results_summary.csv" ]; then
  python - "${RUN_DIR}/results_summary.csv" <<'PYEOF' | tee -a "$STATUS"
import pandas as pd,sys
d=pd.read_csv(sys.argv[1])
for _,r in d.iterrows():
    fmi=f" FMI={r['fmi']:.2f}" if 'fmi' in d.columns and pd.notna(r.get('fmi')) else ""
    print(f"  {r['label']:<28} {r.get('denominator',''):<16} HR={r['hr']:.3f} "
          f"[{r['ci_low']:.3f}-{r['ci_high']:.3f}] n={int(r['n'])}{fmi}")
print("  (published PARADIGM-HF HR = 0.80 [0.73-0.87])")
PYEOF
fi
# EF balance sanity (should now be ~0.5 pre, NOT 0.055) — confirms bounds fix
if [ -f "${RUN_DIR}/balance_table_PSM.csv" ]; then
  python - "${RUN_DIR}/balance_table_PSM.csv" <<'PYEOF' | tee -a "$STATUS"
import pandas as pd,sys
d=pd.read_csv(sys.argv[1]).set_index('covariate')
for c in ['ef_at_index','ef_at_index_missing','lab_egfr','vital_sbp']:
    if c in d.index:
        pre=d.loc[c].get('smd_pre'); post=d.loc[c].get('smd_post'); cc=d.loc[c].get('smd_pre_cc')
        print(f"  balance {c:<20} pre={pre if pd.isna(pre) else round(pre,3)} "
              f"post={post if pd.isna(post) else round(post,3)} cc_pre={cc if pd.isna(cc) else round(cc,3)}")
PYEOF
fi
note "outputs in: ${RUN_DIR}"
note "  results_summary.csv  balance_table_PSM.csv  love_plot_PSM.png  forest.png"
note "  denominator_audit.csv  missingness_audit.csv  feature_inventory.csv"
note "DONE ✓  ($(date +%H:%M:%S))"
