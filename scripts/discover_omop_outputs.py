#!/usr/bin/env python3
"""Bounded read-only output discovery and parquet schema comparison on the H100."""
import argparse
from collections import deque
import json
import os
from pathlib import Path
import sys

from audit_existing_omop import TABLES, schema

SKIP = {'.git', '.venv', '__pycache__', 'node_modules', 'archive', 'rejected'}
TABLE_NAMES = set(TABLES) | {'observation_occurrence', 'drugs', 'drug', 'conditions'}


def inspect_root(root, max_depth, max_entries, max_schemas):
    result = {'root': str(root), 'status': 'running', 'entries_seen': 0,
              'directories_seen': 0, 'depth_limited_directories': 0,
              'symlinks_skipped': 0, 'errors': 0, 'table_directories': [],
              'parquet_files_seen': 0, 'schema_samples': [], 'manifests_seen': []}
    if root.is_symlink():
        result['status'] = 'root_symlink_not_followed'
        return result
    try:
        if not root.is_dir():
            result['status'] = 'root_missing_or_not_directory'
            return result
    except OSError:
        result['status'] = 'root_unavailable'
        return result
    queue = deque([(root, 0)])
    sampled = set()
    capped = False
    while queue and not capped:
        directory, depth = queue.popleft()
        result['directories_seen'] += 1
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if result['entries_seen'] >= max_entries:
                        capped = True
                        break
                    result['entries_seen'] += 1
                    path = Path(entry.path)
                    if entry.is_symlink():
                        result['symlinks_skipped'] += 1
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        if entry.name in SKIP:
                            continue
                        if entry.name in TABLE_NAMES:
                            result['table_directories'].append(str(path))
                        if depth < max_depth:
                            queue.append((path, depth + 1))
                        else:
                            result['depth_limited_directories'] += 1
                    elif entry.is_file(follow_symlinks=False):
                        if entry.name == 'manifest.json':
                            result['manifests_seen'].append(str(path))
                        if path.suffix.lower() != '.parquet':
                            continue
                        result['parquet_files_seen'] += 1
                        # One sample per table and filename family. Labs and vitals
                        # in the same measurement directory get separate chances.
                        parent = next((p for p in path.parents if p.name in TABLE_NAMES and
                                       (p == root or root in p.parents)), path.parent)
                        family = path.stem.split('_')[0]
                        bucket = (str(parent), family)
                        if bucket in sampled or len(sampled) >= max_schemas:
                            continue
                        sampled.add(bucket)
                        result['schema_samples'].append({'path': str(path),
                            'table_candidate': parent.name, **schema(path)})
        except OSError:
            result['errors'] += 1
    result['schema_limit_reached'] = len(sampled) >= max_schemas
    result['status'] = 'entry_limit_reached' if capped else 'bounded_scan_complete'
    return result


def run(roots, output, max_depth=5, max_entries=50000, max_schemas=40):
    if min(max_depth, max_entries, max_schemas) < 1:
        raise ValueError('positive_limits_required')
    if not output.is_absolute() or any(not r.is_absolute() for r in roots):
        raise ValueError('absolute_paths_required')
    output = output.resolve()
    for root in roots:
        resolved = root.resolve()
        if resolved == output or resolved in output.parents or output in resolved.parents:
            raise ValueError('output_overlaps_search_root')
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    report = {'version': 1, 'status': 'running', 'restricted_until_reviewed': True,
              'data_rows_read': False, 'sources_modified': False,
              'limits_per_root': {'max_depth': max_depth, 'max_entries': max_entries,
                                  'max_schema_samples': max_schemas},
              'selection': 'breadth-first directories; first encountered file per table/name family',
              'limitations': ['No row values, concept frequencies or mapping accuracy assessed.',
                              'Partial/add-on tables are not assumed complete OMOP datasets.',
                              'Missing tables cannot be ruled out beyond scan limits or inaccessible paths.',
                              'Schema samples do not establish consistency across all files.'], 'roots': []}
    def save():
        tmp = output / 'summary.json.tmp'
        tmp.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        tmp.replace(output / 'summary.json')
    save()
    for i, root in enumerate(roots, 1):
        print(f'Inspecting location {i}/{len(roots)}...', flush=True)
        item = inspect_root(root, max_depth, max_entries, max_schemas)
        report['roots'].append(item)
        print(f'Location {i}: {item["status"]}; {len(item["schema_samples"])} schema samples', flush=True)
        save()
    report['status'] = 'discovery_complete'
    save()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', action='append', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--max-depth', type=int, default=5)
    parser.add_argument('--max-entries', type=int, default=50000)
    parser.add_argument('--max-schemas', type=int, default=40)
    args = parser.parse_args(argv)
    try:
        run(args.root, args.output_dir, args.max_depth, args.max_entries, args.max_schemas)
    except (OSError, ValueError):
        print('Discovery stopped: check paths, limits and a fresh separate output directory.', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
