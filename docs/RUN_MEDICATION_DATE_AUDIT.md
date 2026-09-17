# Check order timestamp format against medication start date

Reviewed first 500,000-record result: ORDER_INST has 495,563 minute-precision ISO
timestamps and 4,437 literal NULLs; START_DATE has 223,476 ISO dates and 276,524
NULLs. All non-null values parsed. Among 219,039 comparable records, 153,688 are
same-day (70.16%), 63,328 start before order, and 2,023 start after order.
These prefix proportions are not population estimates. The old order-date parsing
failure was a missing minute-precision format in the audit, not evidence of invalid
source dates. The general quality parser now recognizes this format too.

Next run this date audit with `--full-scan` in a fresh directory and review the
restricted mode/class groups. This checks full-source date differences; it does
not establish which date represents new prescribing versus historical information.

Ryan runs on H100. This is read-only, aggregate reconnaissance, not an index rule.
Uses the reviewed literal-tab schema. No patient/date values or record examples
are emitted. No SQLite patient counts are built. No additional dependencies.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte-audits
MED_DATE_OUT=$(mktemp -d "/mnt/raid0/rbc58/ecg-tte-audits/medication-dates-XXXXXXXX")
python scripts/audit_medication_dates.py \
  --root /home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG/Data-2026-04-15 \
  --file CarDS_2435227_Meds.txt \
  --output-dir "$MED_DATE_OUT/report" \
  --expected-schema-sha256 61f9556c4f054c3346d46f78e63d65a467e022f800fb0b388e5dbcf622903da8 \
  --max-rows 500000
cat "$MED_DATE_OUT/report/summary.json"
```

Return the reviewed summary first. This prefix is not random and does not establish
whole-population proportions. If it resolves the timestamp format, use a new output
directory and `--full-scan` instead of `--max-rows` for full-file assessment.

The summary provides field-format counts, masked structural patterns (every digit
and letter erased), and calendar-day comparison counts: same day; start before or
after order by 1–7, 8–30, 31–365 or over 365 days; or not comparable. No exact dates
or individual intervals are exported. Shape catalog omissions are explicit at 100
shapes per field. A record is bounded at 1 MiB; bad widths abort without partial
comparison results. Existing sources/reports remain unchanged.

Candidate formats cover ISO dates/times with minutes, seconds, fractional seconds
up to nine digits, year-first AM/PM timestamps and slash dates/times. Submicrosecond
digits are truncated only for calendar-date parsing. Ambiguous slash dates are not
compared; neither are offset-bearing timestamps. Comparisons of unzoned dates are
calendar comparisons only, not verified temporal order within a day or across time
zones. Recognized candidate null markers remain separately reported. Unsupported
format does not mean clinically invalid data. No parser chooses a new index field.

`restricted_groups.json` contains the same comparisons/format counts stratified by
ORDERING_MODE × ORDER_CLASS, where available. Its 1,000-group cap and omitted records
are explicit. Review labels and counts locally; share approved aggregates only.
Counts are records, not distinct patients, initiators or verified fills. A mode label
is not independently verified encounter setting. Agreement between dates cannot
establish that either represents dispensing or actual treatment initiation.

Next decisions require date-format and source-semantic review, including backdated
history, future scheduled starts, observation history and information available at
the candidate index. Do not automatically fall back to START_DATE for missing order
timestamps. Source dictionaries and the chosen trial determine the justified rule.
