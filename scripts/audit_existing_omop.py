#!/usr/bin/env python3
"""Read existing OMOP manifests and parquet schemas; never run ETL or read rows."""
import argparse
import json
from pathlib import Path
import sys

TABLES = ('person', 'death', 'cohort', 'observation_period', 'condition_occurrence',
          'observation', 'drug_exposure', 'measurement', 'visit_occurrence',
          'procedure_occurrence')
# Do not copy raw exception messages, top-unmapped values, credentials, or logs.
AUDIT_KEYS = ('source_files', 'rows_read', 'kept', 'rows_staged', 'skipped',
              'output_counts', 'rejected_total', 'rejected_by_reason',
              'rxnorm_mapped', 'rxnorm_unmapped', 'rxnorm_map_rate', 'lab_map_rate',
              'mode', 'persons_without_end_date', 'missing_columns')


def safe_regular(path, root):
    try:
        relative = path.relative_to(root)
        current = root
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                return False
        return path.is_file()
    except (ValueError, OSError):
        return False


def schema(path):
    try:
        import pyarrow.parquet as pq
    except ImportError:
        return {'status': 'unavailable', 'reason': 'pyarrow_not_installed'}
    try:
        # Footer/schema metadata only. No read(), read_table(), or row-group read.
        with pq.ParquetFile(path) as reader:
            return {'status': 'available', 'rows_in_footer': reader.metadata.num_rows,
                    'columns': {f.name: str(f.type) for f in reader.schema_arrow}}
    except Exception:
        return {'status': 'unavailable', 'reason': 'parquet_metadata_read_failed'}


def manifest_summary(path):
    with path.open('rb') as stream:
        raw = stream.read(16 * 1024 * 1024 + 1)
    if len(raw) > 16 * 1024 * 1024:
        return {'status': 'unavailable', 'reason': 'manifest_exceeds_limit'}
    try:
        data = json.loads(raw)
        result = {k: data[k] for k in ('run_id', 'started_at', 'finished_at', 'stage', 'local') if k in data}
        errors = data.get('errors', {})
        result['error_step_ids'] = list(errors) if isinstance(errors, dict) else ['unrecognized_error_structure']
        result['steps'] = {}
        for step, stages in data.get('steps', {}).items():
            result['steps'][step] = {}
            for stage, audit in stages.items():
                if isinstance(audit, dict):
                    result['steps'][step][stage] = {k: audit[k] for k in AUDIT_KEYS if k in audit}
        result['status'] = 'read'
        return result
    except (ValueError, AttributeError, TypeError):
        return {'status': 'unavailable', 'reason': 'invalid_manifest_structure'}


def run(root, output, manifest_limit=20, schema_limit=3):
    if not root.is_absolute() or not output.is_absolute():
        raise ValueError('absolute_paths_required')
    root, output = root.resolve(), output.resolve()
    if not root.is_dir() or min(manifest_limit, schema_limit) < 1:
        raise ValueError('invalid_root_or_limits')
    # The report must be entirely outside the existing OMOP tree.
    if root == output or root in output.parents or output in root.parents:
        raise ValueError('output_overlaps_existing_omop')
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    result = {'version': 1, 'status': 'running', 'restricted_until_reviewed': True,
              'omop_root': str(root), 'data_rows_read': False,
              'source_modified': False, 'manifests': [], 'gold_tables': {},
              'limitations': ['Manifest history does not prove lineage of every current gold partition.',
                              'Schema samples do not establish whole-table consistency or mapping accuracy.',
                              'No patient-level completeness, balance, or clinical validation performed.']}
    def save():
        tmp = output / 'summary.json.tmp'
        tmp.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        tmp.replace(output / 'summary.json')
    save()
    manifests = [p for p in (root / 'audit' / 'runs').glob('*/manifest.json') if safe_regular(p, root)]
    manifests.sort(key=lambda p: p.stat().st_mtime_ns, reverse=True)
    result['manifests_found'] = len(manifests)
    result['manifests_selected'] = min(len(manifests), manifest_limit)
    result['manifest_selection'] = 'newest filesystem mtime first; not assumed latest successful full ETL'
    for i, p in enumerate(manifests[:manifest_limit], 1):
        try:
            item = manifest_summary(p)
        except OSError:
            item = {'status': 'unavailable', 'reason': 'manifest_read_failed'}
        result['manifests'].append({'relative_path': str(p.relative_to(root)), **item})
        print(f'Manifest {i}: {item["status"]}', flush=True)
        save()
    for table in TABLES:
        directory = root / 'gold' / table
        if directory.is_symlink() or (root / 'gold').is_symlink():
            result['gold_tables'][table] = {'status': 'symlink_not_followed'}
            continue
        paths = sorted(p for p in directory.rglob('*.parquet') if safe_regular(p, root))
        result['gold_tables'][table] = {
            'status': 'present' if paths else 'no_regular_parquet_found',
            'parquet_files': len(paths), 'schema_selection': 'first paths in lexical order',
            'schema_samples': [{'relative_path': str(p.relative_to(root)), **schema(p)}
                               for p in paths[:schema_limit]]}
        print(f'Table {table}: {len(paths)} parquet files', flush=True)
        save()
    result['status'] = 'inspection_complete'
    save()
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--omop-root', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--manifest-limit', type=int, default=20)
    parser.add_argument('--schema-limit', type=int, default=3)
    args = parser.parse_args(argv)
    try:
        run(args.omop_root, args.output_dir, args.manifest_limit, args.schema_limit)
    except (OSError, ValueError):
        print('Inspection stopped: check root, fresh separate output directory and limits.', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
