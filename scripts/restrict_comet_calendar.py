#!/usr/bin/env python3
"""Create the agreed 2015-onward candidate roster; no new clinical exclusions."""
import argparse
from collections import Counter
from datetime import date
import json
import os
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from audit_comet_numeric_candidates import verify, FIELDS, profile
from build_shared_tables import BuildError, digest, atomic_json

VERSION = 'comet_calendar_candidates_v1'
CUTOFF = date(2015, 1, 1)


def partition(rows):
    seen = set()
    kept, excluded = [], []
    for row in rows:
        key = row['patient_key']
        if not key or key in seen:
            raise BuildError('invalid_or_duplicate_patient_key')
        seen.add(key)
        day = row['index_date']
        if type(day) is not date or row['index_year'] != day.year:
            raise BuildError('invalid_or_inconsistent_index_date')
        (kept if day >= CUTOFF else excluded).append(row)
    return kept, excluded


def run(source, output):
    source, output = Path(source), Path(output)
    if any(not p.is_absolute() or p.is_symlink() for p in (source, output)):
        raise BuildError('absolute_nonsymlink_paths_required')
    a, b = source.resolve(), output.resolve()
    if a == b or a in b.parents or b in a.parents:
        raise BuildError('source_output_overlap')
    summary, _, checks = verify(source)
    table = pq.read_table(source / 'restricted_baseline_resolution.parquet')
    rows = table.to_pylist()
    if len(rows) != summary['rows'] or dict(Counter(r['treatment_arm'] for r in rows)) != summary['denominators']:
        raise BuildError('source_roster_mismatch')
    kept, excluded = partition(rows)
    if not kept:
        raise BuildError('empty_calendar_cohort')
    os.umask(0o077)
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    result = dict(version=VERSION, status='building', counts_valid=False,
                  ready_for_mice=False, restricted_until_reviewed=True)
    atomic_json(output / 'summary.json', result)
    try:
        selected = {r['patient_key'] for r in kept}
        names = ['restricted_baseline_resolution.parquet', 'restricted_feature_status.parquet',
                 'restricted_lab_selected_lineage.parquet']
        for name in names:
            original = pq.read_table(source / name)
            if 'patient_key' not in original.column_names:
                raise BuildError('patient_key_column_missing')
            mask = pa.array([key in selected for key in original['patient_key'].to_pylist()])
            pq.write_table(original.filter(mask), output / name)
        atomic_json(output / 'restricted_exclusions.json',
                    [dict(patient_key=r['patient_key'], reason='index_before_2015') for r in excluded])
        availability = []
        for arm in sorted({r['treatment_arm'] for r in kept}):
            group = [r for r in kept if r['treatment_arm'] == arm]
            for field in FIELDS:
                availability.append(dict(arm=arm, feature=field, **profile([r[field] for r in group])))
        if any(digest(p) != h for p, h in checks.items()):
            raise BuildError('source_changed')
        result.update(status='complete_calendar_candidates', counts_valid=True,
                      source_report=str(source), minimum_index_date=CUTOFF.isoformat(),
                      rows=len(kept), denominators=dict(Counter(r['treatment_arm'] for r in kept)),
                      excluded_denominators=dict(Counter(r['treatment_arm'] for r in excluded)),
                      numeric_profiles=availability,
                      interpretation='Calendar restriction only. Original values, baseline windows and HF rule unchanged. No cleaning, imputation, matching or effects. No upper index-date or outcome-follow-up rule frozen.')
        atomic_json(output / 'manifest.json', dict(version=VERSION,
                    input_checksums={str(p): h for p, h in checks.items()},
                    outputs={p.name: digest(p) for p in output.iterdir() if p.name != 'summary.json'},
                    script_sha256=digest(Path(__file__))))
    except Exception as error:
        result.update(status='failed_counts_invalid', counts_valid=False,
                      reason=str(error) if isinstance(error, BuildError) else type(error).__name__)
        raise
    finally:
        atomic_json(output / 'summary.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-report', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    try:
        run(args.source_report, args.output_dir)
    except Exception as error:
        print('Stopped: ' + (str(error) if isinstance(error, BuildError) else type(error).__name__))
        return 1
    print('Calendar cohort complete. Review summary.json locally; not yet MICE-ready.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
