#!/usr/bin/env python3
"""Bounded format/date comparison audit. No dates, patient keys or text exported."""
import argparse
from collections import Counter
from datetime import datetime
import os
from pathlib import Path
import re

from count_medication_evidence import save, failure_reason, CountError
from inspect_jdat_headers import inspect
from medication_quality import missing_kind
from profile_jdat_mapping import BoundedLines

ISO = re.compile(r'^(\d{4}-\d{2}-\d{2})(?:[ T](\d{2}:\d{2})(?::(\d{2})(\.\d{1,9})?)?(Z|[+-]\d{2}:\d{2})?)?$')
SLASH = re.compile(r'^(\d{1,2})/(\d{1,2})/(\d{4})(?: (\d{1,2}:\d{2})(?::(\d{2})(\.\d{1,9})?)?(?: (AM|PM))?)?$', re.I)
YMD_AM = re.compile(r'^\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}(?::\d{2})? [AP]M$', re.I)


def shape(value):
    # Every letter/digit is erased, including month names and unexpected text.
    coded = ''.join('D' if c.isdigit() else 'A' if c.isalpha() else c if c in '-/:. +"' else '?' for c in value[:120])
    return re.sub(r'(D+|A+)', lambda m: m[0][0] + '{' + str(len(m[0])) + '}', coded) + ('[truncated]' if len(value) > 120 else '')


def parse(value):
    """Returns format label and optional date; date comparison is calendar-only."""
    value = value.strip()
    missing = missing_kind(value)
    if missing:
        return missing, None
    m = ISO.fullmatch(value)
    try:
        if m:
            day, minute, sec, fraction, zone = m.groups()
            normalized = day
            if minute:
                normalized += 'T' + minute + ':' + (sec or '00') + ((fraction or '')[:7]) + (zone or '').replace('Z', '+00:00')
            parsed = datetime.fromisoformat(normalized)
            if zone:
                return 'iso_with_offset_not_compared', None
            label = 'iso_date' if not minute else 'iso_minutes' if sec is None else 'iso_seconds_fraction' if fraction else 'iso_seconds'
            return label, parsed.date()
        if YMD_AM.fullmatch(value):
            fmt = '%Y-%m-%d %I:%M:%S %p' if value.count(':') == 2 else '%Y-%m-%d %I:%M %p'
            return 'ymd_am_pm', datetime.strptime(value.upper(), fmt).date()
        m = SLASH.fullmatch(value)
        if m:
            month, day, year, minute, sec, fraction, ampm = m.groups()
            # Validate both month/day interpretations; never silently choose one.
            dates = []
            for a, b in ((month, day), (day, month)):
                text = f'{year}-{int(a):02d}-{int(b):02d}'
                fmt = '%Y-%m-%d'
                if minute:
                    text += ' ' + minute + ':' + (sec or '00')
                    fmt += ' %I:%M:%S' if ampm else ' %H:%M:%S'
                    if fraction:
                        text += fraction[:7]
                        fmt += '.%f'
                    if ampm:
                        text += ' ' + ampm.upper()
                        fmt += ' %p'
                try:
                    dates.append(datetime.strptime(text, fmt).date())
                except ValueError:
                    dates.append(None)
            if dates[0] and dates[1] and dates[0] != dates[1]:
                return 'slash_day_month_ambiguous_not_compared', None
            if dates[0]:
                return 'slash_month_first_unambiguous', dates[0]
            if dates[1]:
                return 'slash_day_first_unambiguous', dates[1]
            return 'invalid_calendar_or_clock', None
    except ValueError:
        return 'invalid_calendar_or_clock', None
    return 'unrecognized_format', None


def compare(order, start):
    if order is None or start is None:
        return 'not_comparable'
    delta = (start - order).days
    if delta == 0:
        return 'same_calendar_day'
    band = '1_7_days' if abs(delta) <= 7 else '8_30_days' if abs(delta) <= 30 else '31_365_days' if abs(delta) <= 365 else 'over_365_days'
    return ('start_before_order_' if delta < 0 else 'start_after_order_') + band


def run(root, relative, output, expected_schema, max_rows=500000):
    root, output = Path(root), Path(output)
    if not root.is_absolute() or not output.is_absolute() or not expected_schema:
        raise ValueError('explicit_paths_and_schema_required')
    root, output = root.resolve(), output.resolve()
    if output == root or root in output.parents or output in root.parents:
        raise ValueError('output_must_be_separate')
    if max_rows is not None and max_rows <= 0:
        raise ValueError('invalid_limit')
    os.umask(0o077)
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    report = {'version': 1, 'status': 'running', 'restricted_until_reviewed': True,
              'source': str(root / relative), 'max_rows': max_rows,
              'parser': 'provisional_literal_tabs_1MiB_record_no_skipping',
              'comparison': 'calendar days only; offset-bearing and ambiguous slash dates excluded; source semantics unvalidated',
              'clinical_index_rule': 'unchanged_not_frozen'}
    save(output / 'summary.json', report)
    rows = 0
    try:
        h = inspect(root, relative)
        if h.get('status') != 'header_candidate':
            raise CountError('invalid_header_or_source')
        if h['schema_sha256'] != expected_schema:
            raise CountError('schema_hash_mismatch')
        if h['delimiter'] != 'tab':
            raise CountError('literal_tabs_requires_tab_header')
        ix = {n: i for i, n in enumerate(h['columns'])}
        if not {'ORDER_INST', 'START_DATE'} <= ix.keys():
            raise ValueError('required_dates_absent')
        formats = {n: Counter() for n in ('ORDER_INST', 'START_DATE')}
        shapes = {n: Counter() for n in formats}
        omitted = Counter()
        comparisons = Counter()
        group_fields = [n for n in ('ORDERING_MODE', 'ORDER_CLASS') if n in ix]
        groups = {}
        source = root / relative
        before = source.stat()
        eof = False
        with source.open('rb') as stream:
            stream.readline(65537)
            lines = BoundedLines(stream, 'utf-8-sig', 1048576)
            while max_rows is None or rows < max_rows:
                lines.used = 0
                try:
                    line = next(lines)
                except StopIteration:
                    eof = True
                    break
                row = line.rstrip('\r\n').split('\t')
                if len(row) != len(ix):
                    raise CountError('row_width_mismatch')
                rows += 1
                dates = []
                labels = []
                for name in formats:
                    value = row[ix[name]].strip()
                    label, day = parse(value)
                    formats[name][label] += 1
                    dates.append(day)
                    labels.append(label)
                    if not missing_kind(value):
                        key = shape(value)
                        if key in shapes[name] or len(shapes[name]) < 100:
                            shapes[name][key] += 1
                        else:
                            omitted[name] += 1
                relation = compare(*dates)
                comparisons[relation] += 1
                group = tuple(row[ix[n]].strip() for n in group_fields)
                if group in groups or len(groups) < 1000:
                    g = groups.setdefault(group, {'comparison': Counter(), 'order_formats': Counter(), 'start_formats': Counter()})
                    g['comparison'][relation] += 1
                    g['order_formats'][labels[0]] += 1
                    g['start_formats'][labels[1]] += 1
                else:
                    omitted['groups'] += 1
                if rows % 100000 == 0:
                    print('Date audit records: ' + str(rows), flush=True)
        after = source.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise CountError('source_changed')
        save(output / 'restricted_groups.json', {'restricted_keep_on_cluster': True,
             'group_fields': group_fields, 'omitted_records': omitted['groups'],
             'groups': [{'values': list(k), **v} for k, v in groups.items()]})
        report.update(status='complete_file' if eof else 'bounded_prefix', rows_read=rows,
            reached_eof=eof, formats=formats, masked_shapes=shapes,
            shape_omitted_records={n: omitted[n] for n in formats},
            comparison_counts=comparisons, group_omitted_records=omitted['groups'],
            schema_sha256=h['schema_sha256'])
    except Exception as exc:
        report.update(status='failed_results_invalid', reason=failure_reason(exc),
                      error_type=type(exc).__name__, diagnostic_records_processed=rows)
    save(output / 'summary.json', report)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', required=True)
    p.add_argument('--file', required=True)
    p.add_argument('--output-dir', required=True)
    p.add_argument('--expected-schema-sha256', required=True)
    scope = p.add_mutually_exclusive_group()
    scope.add_argument('--max-rows', type=int, default=500000)
    scope.add_argument('--full-scan', action='store_true')
    a = p.parse_args()
    try:
        r = run(a.root, a.file, a.output_dir, a.expected_schema_sha256,
                None if a.full_scan else a.max_rows)
    except Exception as exc:
        print('Could not start: ' + type(exc).__name__)
        return 1
    print('Finished: ' + r['status'])
    return 0 if r['status'] in {'complete_file', 'bounded_prefix'} else 1


if __name__ == '__main__':
    raise SystemExit(main())
