#!/usr/bin/env python3
"""Bounded structural diagnostics only. No patient or raw cell values exported."""
import argparse
import csv
import os
from pathlib import Path

from count_medication_evidence import failure_reason, save
from inspect_jdat_headers import inspect, DELIMITERS
from profile_jdat_mapping import BoundedLines


def run(root, relative, output, limit=500000, encoding='utf-8-sig'):
    root, output = Path(root), Path(output)
    if not root.is_absolute() or not output.is_absolute() or limit <= 0:
        raise ValueError('invalid_paths_or_limit')
    root, output = root.resolve(), output.resolve()
    if output == root or root in output.parents or output in root.parents:
        raise ValueError('output_must_be_separate')
    os.umask(0o077)
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    report = {'version': 1, 'status': 'running', 'restricted_until_reviewed': True,
              'source': str(root / relative), 'limit_per_pass': limit,
              'max_record_bytes': 1048576, 'max_field_chars': 1048576,
              'interpretation': 'Format diagnostics only; no patient N, no repaired rows, no approved parser change.'}
    save(output / 'summary.json', report)
    previous = csv.field_size_limit(1048576)
    try:
        header = inspect(root, relative, encoding=encoding)
        if header.get('status') != 'header_candidate':
            report.update(status='diagnostic_failed', reason='header_or_source_unavailable')
            return report
        source = root / relative
        before = source.stat()
        delimiter = DELIMITERS[header['delimiter']]
        width = len(header['columns'])
        report.update(delimiter=header['delimiter'], expected_columns=width,
                      schema_sha256=header['schema_sha256'])
        # Pass 1 reproduces strict logical-record parsing without counting patients.
        strict = {'records_parsed': 0, 'physical_lines_consumed': 0}
        report['strict_csv'] = strict
        with source.open('rb') as stream:
            stream.readline(65537)
            lines = BoundedLines(stream, encoding, 1048576)
            reader = csv.reader(lines, delimiter=delimiter, strict=True)
            try:
                for _ in range(limit):
                    lines.used = 0
                    try:
                        row = next(reader)
                    except StopIteration:
                        strict['status'] = 'reached_eof'
                        break
                    if len(row) != width:
                        strict.update(status='stopped', reason='row_width_mismatch')
                        break
                    strict['records_parsed'] += 1
                    if strict['records_parsed'] % 100000 == 0:
                        print('Strict pass records: ' + str(strict['records_parsed']), flush=True)
                else:
                    strict['status'] = 'bounded_prefix'
            except Exception as exc:
                strict.update(status='stopped', reason=failure_reason(exc), error_type=type(exc).__name__)
            strict['physical_lines_consumed'] = reader.line_num
        save(output / 'summary.json', report)
        # Pass 2 tests physical-line structure under the literal-quote hypothesis.
        # It does NOT create records or recover a cohort from this interpretation.
        physical = {'lines_read': 0, 'matching_width': 0, 'too_few_columns': 0,
                    'too_many_columns': 0, 'lines_with_quotes': 0,
                    'lines_with_field_start_quote': 0, 'unterminated_final_line': 0}
        report['literal_delimiter_physical_lines'] = physical
        with source.open('rb') as stream:
            stream.readline(65537)
            lines = BoundedLines(stream, encoding, 1048576)
            try:
                for _ in range(limit):
                    lines.used = 0
                    try:
                        line = next(lines)
                    except StopIteration:
                        physical['status'] = 'reached_eof'
                        break
                    physical['lines_read'] += 1
                    physical['unterminated_final_line'] += not line.endswith('\n')
                    n = line.count(delimiter) + 1
                    physical['matching_width' if n == width else 'too_few_columns' if n < width else 'too_many_columns'] += 1
                    physical['lines_with_quotes'] += '"' in line
                    physical['lines_with_field_start_quote'] += line.startswith('"') or (delimiter + '"') in line
                    if physical['lines_read'] % 100000 == 0:
                        print('Structure pass lines: ' + str(physical['lines_read']), flush=True)
                else:
                    physical['status'] = 'bounded_prefix'
            except Exception as exc:
                physical.update(status='stopped', reason=failure_reason(exc), error_type=type(exc).__name__)
        after = source.stat()
        changed = (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns)
        report.update(status='source_changed_diagnostics_invalid' if changed else 'diagnostic_complete',
                      source_changed=changed)
    except Exception as exc:
        report.update(status='diagnostic_failed', reason=failure_reason(exc), error_type=type(exc).__name__)
    finally:
        csv.field_size_limit(previous)
        save(output / 'summary.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--file', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--max-records', type=int, default=500000)
    parser.add_argument('--encoding', choices=['utf-8-sig', 'latin-1'], default='utf-8-sig')
    args = parser.parse_args()
    try:
        result = run(args.root, args.file, args.output_dir, args.max_records, args.encoding)
    except Exception as exc:
        print('Could not start: ' + type(exc).__name__, flush=True)
        return 1
    print('Finished: ' + result['status'], flush=True)
    return 0 if result['status'] == 'diagnostic_complete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
