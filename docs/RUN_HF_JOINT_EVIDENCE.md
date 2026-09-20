# Exploratory joint HF diagnosis and latest-EF evidence

This is a feasibility audit, not an eligible COMET cohort. It uses the existing
lexical medication anchors and preserves patient keys and source/date limitations.
No outcome or imputation is used. The 365-day echo lookback is an explicit
exploratory setting, not a frozen trial criterion; all anchor years are retained.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
HF_JOINT_OUT=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/hf-joint-evidence-XXXXXXXX)
python scripts/audit_hf_sources.py \
  --root /home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG/Data-2026-04-15 \
  --echo /mnt/raid0/rbc58/mm_vhd/metadata/echo_accession_number.parquet \
  --output-dir "$HF_JOINT_OUT/report" \
  --dx-full-scan \
  --allow-hospital-terminal-empty-line \
  --allow-outpatient-terminal-empty-line \
  --joint-echo-window-days 365
cat "$HF_JOINT_OUT/report/summary.json"
```

New `joint_hf_ef_evidence` cross-counts are mutually exclusive within each arm,
anchor year and diagnosis-date view. Views and arms overlap; never sum across them.
The latest strictly prior echo is selected regardless of missingness, with no
older-valid-EF fallback. Stale/missing, numeric bands and latest-day disagreements
remain separate. A code plus above-threshold EF can reflect recovery or timing,
not necessarily an erroneous diagnosis. The >1–35 band is a descriptive numeric
band, not confirmed EF units, the final trial boundary or symptomatic HF.

The explicit provisional code search in hf_joint_evidence.py covers selected I50
codes including I50.2x systolic and I50.4x combined systolic/diastolic families.
Reference: https://ftp.cdc.gov/pub/health_statistics/nchs/publications/ICD10CM/2020/icd10cm_tabular_2020.pdf
This is not an exhaustive HF phenotype or an annual vocabulary validation. ICD9,
hypertensive/other HF code families, free text and malformed cells are not mapped.
Any malformed token makes the entire cell unresolved rather than partially
accepted; existing tokenization counts quantify these cells. CURRENT_ICD10_LIST
may be a retrospective mapping; no claim of historical code availability is made.
One prior code is sufficient for discovery only, not a validated clinical algorithm.

DX_DATE and CALC_DX_DATE are independent views, not fallbacks or pooled evidence.
Within each view, prior codes across both diagnosis files are deduplicated by
patient/arm. Same-day, later and unusably dated code evidence is counted separately;
none qualifies as prior. No prior code found does not mean HF absent. No fixed DX
lookback is applied; clinical diagnosis recency remains to be specified.

Interpretation targets: prior HF code plus recent low-EF evidence; prior systolic
code with missing/stale EF; and other/discordant patterns requiring review. Keep
missing, stale, invalid and disagreement categories separate rather than forcing
all records into those three labels. No eligibility facts are imputed.

Twenty-two synthetic tests across HF source/medication and joint-evidence modules
pass, including time boundaries, duplicate diagnosis rows, separate date views,
malformed code cells, latest echo missingness and privacy. Real joint H100 run is
pending. Full sources are rescanned; no prior aggregate report contains this joint
information. All reports and temporary SQLite files stay under the RAID run root.
