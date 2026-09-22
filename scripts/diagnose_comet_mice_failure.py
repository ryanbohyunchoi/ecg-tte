#!/usr/bin/env python3
"""Report allowlisted failure categories from a private log without printing its text."""
import argparse
import json
from pathlib import Path

PATTERNS = {
    'startup_abi_mismatch': ('startup_abi_mismatch', 'abi version mismatch'),
    'insufficient_ordered_bp_donors': ('insufficient_ordered_bp_donors',),
    'missing_mice_or_jsonlite': ('missing_mice_or_jsonlite',),
    'missing_r_package': ('there is no package called',),
    'r_shared_library_load_failure': ('unable to load shared object', 'error while loading shared libraries'),
    'r_package_load_failure': ('package or namespace load failed',),
    'r_temp_directory_failure': ('cannot create', 'r_tempdir'),
    'model_columns_mismatch': ('model_columns_mismatch',),
    'contrasts_single_level': ('contrasts can be applied only to factors with 2 or more levels',),
    'singular_model': ('system is computationally singular', 'system is exactly singular'),
    'rscript_file_open_failure': ('cannot open file',),
}


def classify(text):
    lower = text.lower()
    return [name for name, patterns in PATTERNS.items()
            if (all(p in lower for p in patterns) if name == 'r_temp_directory_failure' else any(p in lower for p in patterns))]


def diagnose(report):
    summary = json.loads((report / 'summary.json').read_text())
    if summary.get('version') not in ('comet_mice_pilot_v1', 'comet_mice_pilot_v2_ordered_bp') or summary.get('status') != 'failed_pilot':
        raise ValueError('failed_pilot_report_required')
    log = report / 'restricted_engine.log'
    with log.open('rb') as stream:
        sample = stream.read(1048577)
    categories = classify(sample[:1048576].decode('utf-8', errors='replace'))
    return dict(version='comet_mice_failure_diagnostic_v1', log_present=True,
                log_truncated=len(sample)>1048576, categories=categories or ['unclassified_review_locally'],
                interpretation='Fixed pattern matches only; no raw log text or patient values. Does not rerun or alter the pilot.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    try:
        if not args.report.is_absolute(): raise ValueError('absolute_report_path_required')
        result = diagnose(args.report)
    except Exception as error:
        print(json.dumps({'status':'diagnostic_failed','error_type':type(error).__name__}))
        return 1
    print(json.dumps(result,indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
