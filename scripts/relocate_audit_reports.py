#!/usr/bin/env python3
"""Move known project audit folders on H100; no source datasets are selected."""
import argparse
import json
import os
from pathlib import Path
import shutil

PREFIXES = ('jdat-inventory-', 'jdat-headers-', 'jdat-selected-headers-',
            'jdat-mapping-', 'existing-omop-audit-', 'rbc-omop-audit-',
            'rbc-output-discovery-', 'medication-settings-', 'medication-dates-',
            'medication-evidence-counts-', 'medication-format-',
            'medication-literal-counts-', 'medication-quality-', 'hf-medication-screen-')
FINISHED = {'complete', 'complete_file', 'bounded_prefix', 'failed',
            'failed_counts_invalid', 'failed_results_invalid', 'diagnostic_complete',
            'diagnostic_failed', 'source_changed_diagnostics_invalid',
            'inspection_complete', 'inspection_incomplete', 'partial',
            'bounded_scan_complete', 'entry_limit_reached', 'no_files',
            'audit_complete', 'discovery_complete'}


def relocate(sources, destination, execute=False):
    destination = Path(destination)
    if not destination.is_absolute() or destination.is_symlink():
        raise ValueError('destination_must_be_absolute_nonsymlink')
    destination = destination.resolve()
    for source in sources:
        source = Path(source).resolve()
        if source == destination or source in destination.parents or destination in source.parents:
            raise ValueError('source_and_destination_must_be_separate')
    os.umask(0o077)
    if execute:
        destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    results = []
    for source in sources:
        source = Path(source)
        if not source.is_dir() or source.is_symlink():
            continue
        for folder in sorted(source.iterdir()):
            if not folder.name.startswith(PREFIXES) or not folder.is_dir() or folder.is_symlink():
                continue
            target = destination / folder.name
            reason = None
            if target.exists() or target.is_symlink():
                reason = 'destination_exists_no_overwrite'
            summaries = [p for p in (folder/'summary.json', folder/'report'/'summary.json') if p.exists()]
            if not summaries:
                reason = reason or 'no_summary_check_manually'
            for summary in summaries:
                try:
                    if summary.is_symlink():
                        raise ValueError('symlink')
                    # Bounded metadata read; raw parser exceptions are not printed.
                    with summary.open() as f:
                        value = f.read(8 * 1024 * 1024 + 1)
                    if len(value) > 8 * 1024 * 1024:
                        raise ValueError('oversized')
                    status = json.loads(value).get('status')
                    if status not in FINISHED:
                        reason = reason or 'running_or_unrecognized_status_check_manually'
                except Exception:
                    reason = reason or 'unreadable_summary_check_manually'
            if reason:
                action = 'SKIP ' + reason
            elif execute:
                try:
                    shutil.move(str(folder), str(target))
                    action = 'MOVED'
                except Exception as exc:
                    action = 'FAILED ' + type(exc).__name__ + ' inspect_source_and_destination_before_retry'
            else:
                action = 'WOULD_MOVE'
            print(action + ': ' + folder.name, flush=True)
            results.append((folder.name, action))
    print('Destination: ' + str(destination), flush=True)
    if not results:
        print('No matching audit folders found in the selected source locations.', flush=True)
    return results


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute', action='store_true', help='Move finished reports; otherwise preview only')
    args = p.parse_args()
    try:
        results = relocate([Path.home(), Path('/mnt/raid0/rbc58/ecg-tte-audits')],
                           Path('/mnt/raid0/rbc58/ecg-tte/audits'), args.execute)
    except Exception as exc:
        print('Could not start: ' + type(exc).__name__)
        return 1
    return int(any(action.startswith('FAILED') for _, action in results))


if __name__ == '__main__':
    raise SystemExit(main())
