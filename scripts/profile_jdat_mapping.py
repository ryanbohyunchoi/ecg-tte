#!/usr/bin/env python3
"""Restricted, bounded JDAT mapping reconnaissance. No source values on stdout."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

from inspect_jdat_headers import inspect, DELIMITERS

# Only these reviewed code-bearing fields enter the restricted code catalog.
# Values are opaque: ICD list fields are NOT split or interpreted automatically.
CODE_FIELDS = {
    'CURRENT_ICD9_LIST', 'CURRENT_ICD10_LIST', 'CPT_CODE', 'REF_BILL_CODE',
    'REF_BILL_CODE_SET_C', 'REF_BILL_CODE_SET', 'MEDICATION_ID', 'COMPONENT_ID',
    'FLO_MEAS_ID', 'ENC_TYPE_C', 'MAR_ACTION_C', 'ORDER_STATUS_C',
}
TIME_FIELDS = {
    'DX_DATE', 'FIRST_MHX_CONTACT_DATE', 'LAST_MHX_CONTACT_DATE',
    'MEDICAL_HX_DATE', 'MED_HX_START_DT', 'DATE_OF_ENTRY', 'NOTED_DATE',
    'RESOLVED_DATE', 'DELETED_DATE', 'ORDER_INST', 'START_DATE', 'END_DATE',
    'DISCONTINUE_TIME', 'CONTACT_DATE', 'HOSP_ADMSN_DATE', 'HOSP_DISCH_DATE',
    'CPT_DATE', 'PROC_DATE', 'RECORDED_TIME', 'TAKEN_TIME', 'INFUSION_END_TIME',
    'LAB_DATE', 'LAB_TIME', 'ORDER_ENTRY_DATE', 'ORDER_ENTRY_TIME', 'ORDERING_DATE',
    'SPECIMN_TAKEN_DATE', 'SPECIMN_TAKEN_TIME', 'FIRST_RESULT_DATE',
    'FIRST_RESULT_TIME', 'LAST_RESULT_DATE', 'LAST_RESULT_TIME', 'RESULT_DATE',
    'RESULT_TIME',
}
OTHER_FIELDS = {'PAT_ID', 'PAT_MRN_ID', 'PAT_ENC_CSN_ID', 'HSP_ACCOUNT_ID',
                'UNIT', 'MEDICATION_UNIT', 'DOSE_UNIT', 'ORD_VALUE',
                'ORD_NUM_VALUE', 'ORD_NUM_VALUE_CALC', 'MEAS_VALUE'}


class AuditError(Exception):
    pass


class BoundedLines:
    """Bound both multiline CSV records and physical lines before allocating them."""
    def __init__(self, stream, encoding, limit):
        self.stream, self.encoding, self.limit = stream, encoding, limit
        self.used = 0

    def __iter__(self):
        return self

    def __next__(self):
        raw = self.stream.readline(self.limit - self.used + 1)
        if not raw:
            raise StopIteration
        self.used += len(raw)
        if self.used > self.limit:
            raise AuditError('record_exceeds_byte_limit')
        if b'\x00' in raw:
            raise AuditError('nul_byte_in_record')
        return raw.decode(self.encoding, errors='strict')


def save(output, summary):
    temporary = output / 'summary.json.tmp'
    temporary.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    temporary.replace(output / 'summary.json')


def profile(root, entry, ordinal, connection, max_rows, max_record_bytes, progress):
    relative = entry['relative_path']
    checked = inspect(root, relative, entry['encoding'], entry['delimiter'])
    result = {'file_index': ordinal, 'status': 'running', 'rows_accepted': 0,
              'rows_seen': 0, 'fields': {}, 'mapping_status': 'not_assessed'}
    if checked.get('status') != 'header_candidate':
        result.update(status='failed', reason=checked.get('reason', 'header_rejected'))
        return result
    if checked['schema_sha256'] != entry['schema_sha256']:
        result.update(status='failed', reason='schema_changed_since_header_report')
        return result
    names = checked['columns']
    selected = [(i, n) for i, n in enumerate(names)
                if n in CODE_FIELDS | TIME_FIELDS | OTHER_FIELDS]
    result['schema_sha256'] = checked['schema_sha256']
    result['fields'] = {n: {'empty': 0, 'nonempty': 0} for _, n in selected}
    result['time_validation'] = 'presence_only_semantics_and_formats_unverified'
    result['missingness_policy'] = 'empty_or_whitespace_only; literal null markers remain nonempty'
    source = root / relative
    before = source.stat()
    result['source_stat'] = {'bytes': before.st_size, 'mtime_ns': before.st_mtime_ns}
    try:
        with source.open('rb') as stream:
            stream.readline(65537)  # Already validated bounded header.
            lines = BoundedLines(stream, entry['encoding'], max_record_bytes)
            reader = csv.reader(lines, delimiter=DELIMITERS[entry['delimiter']], strict=True)
            while result['rows_accepted'] < max_rows:
                lines.used = 0
                try:
                    row = next(reader)
                except StopIteration:
                    result['status'] = 'complete_file'
                    break
                result['rows_seen'] += 1
                if len(row) != len(names):
                    raise AuditError('row_width_mismatch')
                for i, name in selected:
                    value = row[i].strip()
                    result['fields'][name]['nonempty' if value else 'empty'] += 1
                    if value and name in CODE_FIELDS:
                        if len(value) > 4096:
                            raise AuditError('code_cell_exceeds_limit')
                        connection.execute(
                            'INSERT INTO codes VALUES (?, ?, ?, 1) '
                            'ON CONFLICT(file_index, field, source_value) '
                            'DO UPDATE SET record_count=record_count+1', (ordinal, name, value))
                result['rows_accepted'] += 1
                if result['rows_accepted'] % progress == 0:
                    connection.commit()
                    print(f'File {ordinal}: {result["rows_accepted"]} rows accepted', flush=True)
            else:
                # Do not read an extra patient record merely to prove EOF.
                result['status'] = 'bounded_prefix'
        after = source.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise AuditError('source_changed_during_scan')
    except AuditError as exc:
        result.update(status='failed', reason=str(exc))
    except (UnicodeError, csv.Error):
        result.update(status='failed', reason='decode_or_csv_parse_failed')
    except OSError:
        result.update(status='failed', reason='filesystem_error')
    # Partial failed-file counts cannot be mistaken for valid evidence.
    if result['status'] == 'failed':
        connection.execute('DELETE FROM codes WHERE file_index=?', (ordinal,))
        result['fields'] = {}
        result['counts_valid'] = False
    else:
        result['counts_valid'] = True
        for _, name in selected:
            if name in CODE_FIELDS:
                count = connection.execute('SELECT COUNT(*) FROM codes WHERE file_index=? AND field=?',
                                           (ordinal, name)).fetchone()[0]
                result['fields'][name]['distinct_raw_cells'] = count
    connection.commit()
    return result


def run(headers, indices, output, max_rows=100000, max_record_bytes=1048576, progress=10000):
    if min(max_rows, max_record_bytes, progress) <= 0:
        raise AuditError('limits_must_be_positive')
    raw = headers.read_bytes()
    manifest = json.loads(raw)
    root = Path(manifest['source_root'])
    if not root.is_absolute() or not root.is_dir():
        raise AuditError('source_root_unavailable')
    root = root.resolve()
    output = output.resolve()
    if output == root or root in output.parents or output in root.parents:
        raise AuditError('output_overlaps_source')
    entries = manifest['files']
    if not indices or len(indices) != len(set(indices)):
        raise AuditError('explicit_unique_file_indices_required')
    chosen = []
    for index in indices:
        if index < 1 or index > len(entries):
            raise AuditError('file_index_out_of_range')
        entry = entries[index - 1]
        if entry.get('status') != 'header_candidate':
            raise AuditError('selected_header_not_accepted')
        chosen.append((index, entry))
    paths = [entry['relative_path'] for _, entry in chosen]
    if len(paths) != len(set(paths)):
        raise AuditError('duplicate_selected_path')
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    summary = {'version': 1, 'status': 'running', 'restricted': True,
               'header_report_sha256': hashlib.sha256(raw).hexdigest(),
               'source_root': str(root), 'max_rows_per_file': max_rows,
               'max_record_bytes': max_record_bytes,
               'scope': 'per-file prefix; not random; no pooling or patient-level coverage',
               'standard_mapping': 'not_assessed', 'tokenizer_coverage': 'not_assessed',
               'files': []}
    save(output, summary)
    csv.field_size_limit(max_record_bytes)
    with sqlite3.connect(output / 'restricted_code_counts.sqlite') as connection:
        connection.execute('PRAGMA cache_size=-8192')
        connection.execute('CREATE TABLE codes (file_index INTEGER, field TEXT, source_value TEXT, '
                           'record_count INTEGER, PRIMARY KEY (file_index, field, source_value)) WITHOUT ROWID')
        for index, entry in chosen:
            print(f'Profiling file {index}...', flush=True)
            result = profile(root, entry, index, connection, max_rows, max_record_bytes, progress)
            summary['files'].append(result)
            save(output, summary)
            print(f'File {index}: {result["status"]}', flush=True)
    summary['status'] = 'failed' if any(f['status'] == 'failed' for f in summary['files']) else 'audit_complete'
    save(output, summary)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--headers', type=Path, required=True, help='Existing header summary.json')
    parser.add_argument('--file-index', type=int, action='append', required=True,
                        help='1-based entry in header report; repeat explicitly')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--max-rows', type=int, default=100000)
    parser.add_argument('--max-record-bytes', type=int, default=1048576)
    parser.add_argument('--progress-every', type=int, default=10000)
    args = parser.parse_args(argv)
    try:
        result = run(args.headers, args.file_index, args.output_dir, args.max_rows,
                     args.max_record_bytes, args.progress_every)
        return 2 if result['status'] == 'failed' else 0
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error, AuditError):
        print('Audit stopped: setup or storage failure. Check paths, selection and available space; '
              'any running report is incomplete.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
