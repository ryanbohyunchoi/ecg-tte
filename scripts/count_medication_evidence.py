#!/usr/bin/env python3
"""Read-only raw JDAT counts; candidate fields do not verify pharmacy fills."""
import argparse
from collections import Counter
import csv
import json
import os
from pathlib import Path
import sqlite3
import tempfile

from inspect_jdat_headers import inspect, DELIMITERS
from profile_jdat_mapping import BoundedLines, AuditError

FILL = {'FILL_DATE', 'DISPENSE_DATE', 'DISPENSING_DATE', 'DISPENSED_DATE'}
SUPPLY = {'DAYS_SUPPLY', 'DAYS_SUPPLIED'}
OTHER = {'REFILLS', 'REFILLS_REMAINING', 'QUANTITY', 'DISP_QUANTITY',
         'ORDER_INST', 'START_DATE', 'END_DATE', 'TAKEN_TIME',
         'ORDER_MED_ID', 'PAT_ENC_CSN_ID', 'MAR_ACTION', 'DISCONTINUE_TIME'}
CATEGORY = ('ORDER_CLASS', 'ORDER_STATUS')


class CountError(Exception):
    """Static diagnostics authored here, never source contents."""


def failure_reason(exc):
    if isinstance(exc, CountError) and str(exc) in {
        'invalid_header_or_source', 'patient_key_absent', 'row_width_mismatch', 'source_changed'
    }:
        return str(exc)
    if isinstance(exc, AuditError) and str(exc) in {
        'record_exceeds_byte_limit', 'nul_byte_in_record'
    }:
        return str(exc)
    if isinstance(exc, csv.Error):
        if str(exc).startswith('field larger than field limit ('):
            return 'csv_field_exceeds_character_limit'
        if str(exc) == 'unexpected end of data':
            return 'csv_unterminated_quoted_record'
        if str(exc).endswith(" expected after '\"'"):
            return 'csv_unexpected_character_after_closing_quote'
        return 'csv_parse_error'
    if isinstance(exc, UnicodeError):
        return 'text_decode_error'
    if isinstance(exc, sqlite3.Error):
        return 'count_database_error'
    if isinstance(exc, OSError):
        return 'filesystem_error'
    return 'unexpected_error'


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def run(root, relative, output, patient_column='PAT_MRN_ID', max_rows=100000,
        encoding='utf-8-sig', category_limit=1000, max_record_bytes=1048576,
        max_field_chars=1048576):
    """max_rows=None explicitly requests EOF; counts are per source, never pooled."""
    root, output = Path(root), Path(output)
    if not root.is_absolute() or not output.is_absolute():
        raise ValueError('absolute_paths_required')
    root, output = root.resolve(), output.resolve()
    if output == root or root in output.parents or output in root.parents:
        raise ValueError('output_must_be_separate')
    if (max_rows is not None and max_rows <= 0) or category_limit <= 0:
        raise ValueError('invalid_limit')
    if not 128 <= max_field_chars <= max_record_bytes <= 16777216:
        raise ValueError('invalid_parser_limits')
    if patient_column not in {'PAT_MRN_ID', 'MRN', 'PERSON_ID'}:
        raise ValueError('unsupported_patient_key')
    os.umask(0o077)
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    report = {'version': 2, 'status': 'running', 'restricted_until_reviewed': True,
              'source': str(root / relative), 'max_rows': max_rows,
              'selection': 'full_file_requested' if max_rows is None else 'first_records_not_random',
              'patient_key': patient_column,
              'identity_policy': 'trim_only; nonempty keys are unvalidated, no cross-source reconciliation',
              'presence_policy': 'whitespace_only; literal null markers count as values',
              'verified_outpatient_fill_patients': None,
              'verified_fill_status': 'not_assessable_source_semantics_unverified',
              'eligible_initiator_patients': None,
              'eligibility_status': 'not_assessed_no_trial_contract',
              'parser': {'max_record_bytes': max_record_bytes,
                         'max_field_chars': max_field_chars,
                         'quoting': 'csv_default_strict_no_skipping'}}
    save(output / 'summary.json', report)
    initial_report = dict(report)
    connection = None
    rows = 0
    stage = 'header_validation'
    previous_field_limit = csv.field_size_limit()
    csv.field_size_limit(max_field_chars)
    try:
        header = inspect(root, relative, encoding=encoding)
        if header.get('status') != 'header_candidate':
            raise CountError('invalid_header_or_source')
        names = [name.upper() for name in header['columns']]
        if patient_column not in names:
            raise CountError('patient_key_absent')
        index = {name: i for i, name in enumerate(names)}
        selected = sorted((FILL | SUPPLY | OTHER) & index.keys())
        categories = [name for name in CATEGORY if name in index]
        fields = {name: Counter() for name in selected}
        groups, group_counts = {}, Counter()
        rows = missing_id = omitted = 0
        eof = False
        source = root / relative
        before = source.stat()
        stage = 'count_database_setup'
        # Identifiers exist only in restricted temporary storage on the cluster.
        with tempfile.TemporaryDirectory(prefix='private-counts-', dir=output) as tmp:
            connection = sqlite3.connect(str(Path(tmp) / 'counts.sqlite'))
            connection.execute('PRAGMA temp_store=MEMORY')
            connection.execute('CREATE TABLE members (group_id INTEGER, patient TEXT, PRIMARY KEY(group_id, patient)) WITHOUT ROWID')
            with source.open('rb') as stream:
                stream.readline(65537)
                lines = BoundedLines(stream, encoding, max_record_bytes)
                reader = csv.reader(lines, delimiter=DELIMITERS[header['delimiter']], strict=True)
                while max_rows is None or rows < max_rows:
                    lines.used = 0
                    stage = 'record_parse'
                    try:
                        row = next(reader)
                    except StopIteration:
                        eof = True
                        break
                    if len(row) != len(names):
                        raise CountError('row_width_mismatch')
                    stage = 'record_count'
                    rows += 1
                    patient = row[index[patient_column]].strip()
                    missing_id += not bool(patient)
                    present = set()
                    for name in selected:
                        nonempty = bool(row[index[name]].strip())
                        fields[name]['nonempty' if nonempty else 'empty'] += 1
                        if nonempty:
                            present.add(name)
                    memberships = [-1]
                    if present & FILL:
                        memberships.append(-2)
                    if present & SUPPLY:
                        memberships.append(-3)
                    values = tuple(row[index[name]].strip() for name in categories)
                    if values not in groups and len(groups) < category_limit:
                        groups[values] = len(groups)
                    if values in groups:
                        gid = groups[values]
                        group_counts[gid] += 1
                        memberships.append(gid)
                    else:
                        omitted += 1
                    if patient:
                        connection.executemany('INSERT OR IGNORE INTO members VALUES (?, ?)',
                                               [(gid, patient) for gid in memberships])
                    if rows % 100000 == 0:
                        connection.commit()
                        print('Processed records: ' + str(rows), flush=True)
            stage = 'source_validation'
            after = source.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise CountError('source_changed')
            stage = 'count_aggregation'
            counts = dict(connection.execute('SELECT group_id, COUNT(*) FROM members GROUP BY group_id'))
            connection.close()
            connection = None
        stage = 'report_write'
        report.update(status='complete_file' if eof else 'bounded_prefix',
                      reached_eof=eof, rows_read=rows, rows_missing_patient_key=missing_id,
                      distinct_nonempty_patient_keys=counts.get(-1, 0),
                      fields_present=selected, fields_absent=sorted((FILL | SUPPLY | OTHER) - index.keys()),
                      field_presence={name: {'nonempty': fields[name]['nonempty'], 'empty': fields[name]['empty']} for name in selected},
                      patients_with_candidate_fill_date=(counts.get(-2, 0) if FILL & index.keys() else None),
                      patients_with_candidate_supply=(counts.get(-3, 0) if SUPPLY & index.keys() else None),
                      candidate_interpretation='nonempty only; date/numeric validity and dispensing semantics not validated',
                      category_omitted_records=omitted, schema_sha256=header['schema_sha256'],
                      source_bytes=before.st_size, source_mtime_ns=before.st_mtime_ns)
        save(output / 'restricted_categories.json', {
            'restricted_keep_on_cluster': True, 'category_fields': categories,
            'groups': [{'values': list(values), 'records': group_counts[gid],
                        'distinct_nonempty_patient_keys': counts.get(gid, 0)}
                       for values, gid in groups.items()],
            'omitted_records': omitted,
            'warning': 'Groups and source files overlap in patients; do not sum distinct counts.'})
    except Exception as exc:
        if connection is not None:
            connection.close()
        # Progress is diagnostic only; no patient denominators survive a failure.
        report = initial_report
        report.update(status='failed_counts_invalid', error_type=type(exc).__name__,
                      reason=failure_reason(exc), failure_stage=stage,
                      diagnostic_records_processed=rows, counts_valid=False)
    finally:
        csv.field_size_limit(previous_field_limit)
    save(output / 'summary.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--file', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--patient-column', default='PAT_MRN_ID', choices=['PAT_MRN_ID', 'MRN', 'PERSON_ID'])
    parser.add_argument('--encoding', default='utf-8-sig', choices=['utf-8-sig', 'latin-1'])
    parser.add_argument('--max-record-bytes', type=int, default=1048576)
    parser.add_argument('--max-field-chars', type=int, default=1048576)
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument('--max-rows', type=int, default=100000)
    scope.add_argument('--full-scan', action='store_true')
    args = parser.parse_args()
    try:
        report = run(args.root, args.file, args.output_dir, args.patient_column,
                     None if args.full_scan else args.max_rows, args.encoding,
                     max_record_bytes=args.max_record_bytes, max_field_chars=args.max_field_chars)
    except Exception as exc:
        print('Could not start: ' + type(exc).__name__, flush=True)
        return 1
    print('Finished: ' + report['status'] + '. Review reports on the cluster.', flush=True)
    return 0 if report['status'] in {'complete_file', 'bounded_prefix'} else 1


if __name__ == '__main__':
    raise SystemExit(main())
