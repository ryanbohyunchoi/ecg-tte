#!/usr/bin/env python3
"""Read-only bounded medication reconnaissance; raw categories stay on H100."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path

CATEGORIES = {'setting', 'order_class', 'order_status', 'source_file', 'source',
              'drug_type_concept_id', 'mar_action_c', 'enc_type_c'}
PRESENCE = {'days_supply', 'days_supplied', 'refills', 'refills_remaining',
            'fill_date', 'dispense_date', 'dispensing_date', 'quantity',
            'order_date', 'order_inst', 'start_date', 'end_date',
            'taken_time', 'mar_action_c', 'visit_occurrence_id',
            'pat_enc_csn_id', 'order_med_id'}
CROSS = ('setting', 'order_class', 'order_status', 'source_file')


def write_json(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=True) + '\n')
    temp.replace(path)


def category(value):
    # Null and blank are distinct; no clinical meaning is inferred from labels.
    if value is None:
        return ('null', '')
    value = str(value)
    return ('blank', '') if not value.strip() else ('value', value)


def increment(counter, key, limit):
    if key in counter or len(counter) < limit:
        counter[key] += 1
        return 0
    return 1


def inspect(path, row_limit, category_limit):
    import pyarrow.parquet as pq
    before = path.stat()
    parquet = pq.ParquetFile(path)
    fields = {}
    for name in parquet.schema_arrow.names:
        key = name.lower()
        if key in CATEGORIES | PRESENCE:
            if key in fields:
                raise ValueError('ambiguous_case_insensitive_columns')
            fields[key] = name
    n = min(row_limit, parquet.metadata.num_rows)
    summary = {'file': str(path), 'rows_in_footer': parquet.metadata.num_rows,
               'rows_read': 0, 'selection': 'first_rows_not_random',
               'fields_present': sorted(fields),
               'fields_absent': sorted((CATEGORIES | PRESENCE) - fields.keys()),
               'field_counts': {}, 'cross_fields': [k for k in CROSS if k in fields]}
    counters = {k: Counter() for k in fields if k in CATEGORIES}
    omitted = dict.fromkeys(counters, 0)
    missing = {k: Counter() for k in fields}
    cross = Counter()
    cross_omitted = 0
    if fields and n:
        for batch in parquet.iter_batches(batch_size=min(8192, n), columns=list(fields.values()), use_threads=False):
            batch = batch.slice(0, min(batch.num_rows, n - summary['rows_read']))
            cols = {k: batch.column(batch.schema.get_field_index(v)).to_pylist() for k, v in fields.items()}
            for i in range(batch.num_rows):
                values = {}
                for key, col in cols.items():
                    val = category(col[i])
                    missing[key][val[0]] += 1
                    if key in counters:
                        omitted[key] += increment(counters[key], val, category_limit)
                    if key in CROSS:
                        values[key] = val
                if summary['cross_fields']:
                    cross_omitted += increment(cross, tuple(values[k] for k in summary['cross_fields']), category_limit)
            summary['rows_read'] += batch.num_rows
            if summary['rows_read'] >= n:
                break
    for key in fields:
        summary['field_counts'][key] = {kind: missing[key][kind] for kind in ('null', 'blank', 'value')}
        if key in counters:
            summary['field_counts'][key].update(retained_categories=len(counters[key]), uncatalogued_records=omitted[key])
    summary.update(status='complete' if fields else 'no_allowlisted_columns',
                   row_limit_reached=summary['rows_read'] < parquet.metadata.num_rows,
                   cross_uncatalogued_records=cross_omitted,
                   source_changed=(before.st_size, before.st_mtime_ns) != (path.stat().st_size, path.stat().st_mtime_ns))
    if summary['source_changed']:
        summary['status'] = 'source_changed_results_unreliable'
    restricted = {'file': str(path), 'categories': {
        k: [{'kind': kind, 'value': value, 'records': count} for (kind, value), count in c.most_common()]
        for k, c in counters.items()}, 'cross_fields': summary['cross_fields'],
        'cross_counts': [{'values': [{'kind': kind, 'value': value} for kind, value in key], 'records': count}
                         for key, count in cross.most_common()]}
    return summary, restricted


def run(root, output, row_limit=100000, file_limit=40, category_limit=1000):
    if min(row_limit, file_limit, category_limit) <= 0:
        raise ValueError('limits_must_be_positive')
    root, output = Path(root).resolve(), Path(output).resolve()
    if not root.is_dir():
        raise ValueError('source_directory_unavailable')
    if output == root or root in output.parents or output in root.parents:
        raise ValueError('output_must_be_separate_from_source')
    os.umask(0o077)
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    # Flat directory only: do not walk other cohorts or follow descendant symlinks.
    files = sorted(p for p in root.iterdir() if p.suffix.lower() == '.parquet' and p.is_file() and not p.is_symlink())
    report = {'version': 1, 'status': 'running', 'restricted_until_reviewed': True,
              'source': str(root), 'row_limit_per_file': row_limit, 'category_limit': category_limit,
              'files_discovered': len(files), 'file_limit_reached': len(files) > file_limit,
              'scope': 'flat parquet directory; no patient identifiers or note columns read; record counts only',
              'interpretation': 'No setting semantics, actual fills, adherence, linkage or unique patients validated. Prefixes are not population estimates.',
              'files': []}
    raw = {'restricted_keep_on_cluster': True, 'files': []}
    write_json(output / 'summary.json', report)
    for i, path in enumerate(files[:file_limit], 1):
        print(f'Inspecting file {i}/{min(len(files), file_limit)}', flush=True)
        try:
            result, values = inspect(path, row_limit, category_limit)
            raw['files'].append(values)
        except Exception as exc:
            # Exception messages may contain source data; only the class is retained.
            result = {'file': str(path), 'status': 'failed', 'error_type': type(exc).__name__}
        report['files'].append(result)
        write_json(output / 'restricted_values.json', raw)
        write_json(output / 'summary.json', report)
    report['status'] = ('no_files' if not files else 'inspection_complete' if all(f['status'] == 'complete' for f in report['files']) else 'inspection_incomplete')
    write_json(output / 'summary.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--max-rows-per-file', type=int, default=100000)
    parser.add_argument('--max-files', type=int, default=40)
    parser.add_argument('--max-categories', type=int, default=1000)
    args = parser.parse_args()
    try:
        result = run(args.root, args.output_dir, args.max_rows_per_file, args.max_files, args.max_categories)
    except Exception as exc:
        print('Audit could not start: ' + type(exc).__name__, flush=True)
        return 1
    print('Finished: ' + result['status'] + '. Review reports on the cluster.', flush=True)
    return 0 if result['status'] == 'inspection_complete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
