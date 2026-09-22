#!/usr/bin/env python3
"""Apply agreed minimal cleaning and export a cohort-specific MICE preparation table."""
import argparse
from collections import Counter
import json
import math
import os
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from build_shared_tables import BuildError, digest, atomic_json
from build_comet_cached_baseline import discover
from restrict_comet_calendar import partition

VERSION = 'comet_mice_preparation_v1'


def clean(rows):
    cleaned, changes = [], []
    for original in rows:
        row = dict(original)
        for field in ('dbp', 'bmi'):
            value = row[field]
            if value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value)):
                raise BuildError('invalid_numeric_input')
            reason = ('zero_dbp' if field == 'dbp' and value == 0 else
                      'extreme_bmi_scale' if field == 'bmi' and value is not None and (value < 1 or value > 1000) else None)
            if reason:
                row[field] = None
                changes.append(dict(patient_key=row['patient_key'], feature=field, original_value=value, reason=reason))
        cleaned.append(row)
    return cleaned, changes


def run(source, output):
    source, output = Path(source), Path(output)
    if any(not p.is_absolute() or p.is_symlink() for p in (source, output)):
        raise BuildError('absolute_nonsymlink_paths_required')
    if source.resolve() == output.resolve() or source.resolve() in output.resolve().parents or output.resolve() in source.resolve().parents:
        raise BuildError('source_output_overlap')
    summary = json.loads((source / 'summary.json').read_text())
    manifest = json.loads((source / 'manifest.json').read_text())
    if summary.get('version') != 'comet_calendar_candidates_v1' or manifest.get('version') != summary['version'] or summary.get('status') != 'complete_calendar_candidates' or summary.get('counts_valid') is not True:
        raise BuildError('complete_calendar_cohort_required')
    checks = {source / name: digest(source / name) for name in ('summary.json', 'manifest.json')}
    for name, expected in manifest['outputs'].items():
        path = source / name
        if path.is_symlink() or source.resolve() not in path.resolve().parents or digest(path) != expected:
            raise BuildError('calendar_artifact_changed')
        checks[path] = expected
    name = 'restricted_baseline_resolution.parquet'
    if name not in manifest['outputs']:
        raise BuildError('baseline_missing_from_manifest')
    table = pq.read_table(source / name)
    rows = table.to_pylist()
    kept, excluded = partition(rows)
    if excluded or len(kept) != summary['rows'] or dict(Counter(r['treatment_arm'] for r in kept)) != summary['denominators']:
        raise BuildError('calendar_roster_mismatch')
    cleaned, changes = clean(rows)
    contract = json.loads((Path(__file__).resolve().parents[1] / 'docs/COMET_PSM_TABLE_V2.json').read_text())
    fields = [x['name'] for x in contract['covariates']]
    if not set(fields) <= set(table.column_names):
        raise BuildError('declared_covariates_missing')
    os.umask(0o077)
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    result = dict(version=VERSION, status='building', counts_valid=False, ready_for_mice=False, restricted_until_reviewed=True)
    atomic_json(output / 'summary.json', result)
    try:
        pq.write_table(pa.Table.from_pylist(cleaned, schema=table.schema), output / 'restricted_cleaned_baseline.parquet')
        atomic_json(output / 'restricted_cleaning_log.json', changes)
        missingness = []
        for arm in sorted(summary['denominators']):
            group = [r for r in cleaned if r['treatment_arm'] == arm]
            for field in fields:
                missingness.append(dict(arm=arm, feature=field, rows=len(group), missing=sum(r[field] is None for r in group)))
        if any(digest(p) != h for p, h in checks.items()):
            raise BuildError('inputs_changed')
        result.update(status='complete_mice_preparation', counts_valid=True, rows=len(cleaned), denominators=summary['denominators'],
                      source_report=str(source), changes=[dict(feature=f, reason=r, cells=n) for (f,r),n in sorted(Counter((c['feature'],c['reason']) for c in changes).items())],
                      missingness=missingness, interpretation='Agreed zero DBP and BMI <1 or >1000 become missing. No patients removed, no other values changed. Units remain unverified. Not an imputation run; final model and outcome eligibility remain unresolved.')
        atomic_json(output / 'manifest.json', dict(version=VERSION, input_checksums={str(p):h for p,h in checks.items()},
                    outputs={p.name:digest(p) for p in output.iterdir() if p.name != 'summary.json'}, script_sha256=digest(Path(__file__))))
    except Exception as error:
        result.update(status='failed_counts_invalid', counts_valid=False, reason=str(error) if isinstance(error,BuildError) else type(error).__name__)
        raise
    finally:
        atomic_json(output / 'summary.json', result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-report', type=Path)
    p.add_argument('--output-dir', required=True, type=Path)
    a = p.parse_args()
    try:
        source = a.source_report or discover(Path('/mnt/raid0/rbc58/ecg-tte'), 'audits/comet-calendar-*/report/summary.json', 'comet_calendar_candidates_v1', 'complete_calendar_candidates')
        run(source, a.output_dir)
    except Exception as error:
        print('Stopped: '+(str(error) if isinstance(error,BuildError) else type(error).__name__))
        return 1
    print('Cleaning complete; review summary.json. MICE has not run.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
