# Latest: outpatient DX failure after hospital fix

The HF version 3 run progressed to outpatient DX, then failed row_width_mismatch
near the 9,600,000-record progress message. The exact line and cause are unknown.
Do not repeat the full HF audit unchanged. Run only the outpatient diagnostic:

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
HF_DX_FORMAT_OUT=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/hf-dx-format-XXXXXXXX)
python scripts/diagnose_medication_format.py \
  --root /home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG/Data-2026-04-15 \
  --file CarDS_2435227_Outpatient_Enc_DX.txt \
  --expected-schema-sha256 eee6c9922b68b8f5c95022eff2a9c7b827478195d07167c62343060cb7e75cb4 \
  --output-dir "$HF_DX_FORMAT_OUT/report" \
  --full-scan
cat "$HF_DX_FORMAT_OUT/report/summary.json"
```

Diagnostic version 3 reports byte payload lengths, exact-empty/ASCII-whitespace
flags and final-physical-line status with the capped mismatch samples. It does not
print source text. EOF status remains unknown for a bounded/stopped pass. A BOM
payload is not treated as an empty line. Eleven synthetic diagnostic tests pass.
No outpatient parser exception is enabled by this change.

# Hospital diagnosis format diagnostic

The version 2 HF source audit stopped in CarDS_2435227_Hosp_Enc_DX.txt after its
42,700,000-record progress message with row_width_mismatch. Exact failing ordinal
and cause are not established by that progress message. Its counts are invalid;
no records may be skipped to turn that run into cohort evidence.

Run the updated generic structural diagnostic (historical filename retained).
It reads only this diagnosis file, never medications or echo. Pass one uses strict
CSV quoting and stops on the first parser/width failure or EOF. Pass two checks all
physical-line widths with literal quotes, retaining at most ten mismatch ordinals
and structural properties. It emits no cell contents, patient keys or clinical
 dates. Both interpretations remain hypotheses, not approved ingestion contracts.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
HF_DX_FORMAT_OUT=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/hf-dx-format-XXXXXXXX)
python scripts/diagnose_medication_format.py \
  --root /home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG/Data-2026-04-15 \
  --file CarDS_2435227_Hosp_Enc_DX.txt \
  --expected-schema-sha256 eee6c9922b68b8f5c95022eff2a9c7b827478195d07167c62343060cb7e75cb4 \
  --output-dir "$HF_DX_FORMAT_OUT/report" \
  --full-scan
cat "$HF_DX_FORMAT_OUT/report/summary.json"
```

Review the aggregate report before sharing. diagnostic_complete means the requested
format investigation finished; inspect each pass's status. It does not mean the
source is well formed or the failed HF counts are recovered. A malformed newline,
embedded delimiter, quoted multiline record or other format problem cannot be
inferred merely from a width failure. Existing sources/reports remain untouched.
