#!/usr/bin/env python3
"""HF medication-name feasibility screen. Not a validated drug map or HF cohort."""
import argparse
from collections import Counter
from functools import lru_cache
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile

from audit_medication_dates import parse, compare
from count_medication_evidence import CountError, failure_reason, save
from inspect_jdat_headers import inspect
from medication_quality import missing_kind
from profile_jdat_mapping import BoundedLines

NAMES = ('MEDICATION_NAME', 'GENERIC_NAME', 'SIMPLE_GENERIC')
BUCKETS = ('carvedilol_not_marked_extended_candidate', 'carvedilol_extended_review',
           'metoprolol_tartrate_candidate', 'metoprolol_succinate_review',
           'metoprolol_unspecified_review', 'sacubitril_valsartan_candidate',
           'enalapril_candidate', 'brand_only_review', 'combination_review',
           'conflicting_names_review', 'sacubitril_without_valsartan_review')
PAIR_ARMS = {'COMET': ('carvedilol_not_marked_extended_candidate', 'metoprolol_tartrate_candidate'),
             'PARADIGM_HF': ('sacubitril_valsartan_candidate', 'enalapril_candidate')}
GENERIC = {'carvedilol', 'metoprolol', 'sacubitril', 'enalapril'}
BRANDS = {'coreg', 'coregcr', 'lopressor', 'toprol', 'entresto', 'vasotec', 'epaned', 'vaseretic'}


@lru_cache(maxsize=20000)
def classify(names):
    # Discovery only: aliases are search leads, never sufficient to assign an arm.
    text = ' '.join(names).lower()
    words = set(re.findall(r'[a-z]+', text))
    if not words & (GENERIC | BRANDS):
        return None
    families = set()
    for family, aliases in (
        ('carvedilol', {'carvedilol', 'coreg', 'coregcr'}),
        ('metoprolol', {'metoprolol', 'lopressor', 'toprol'}),
        ('arni', {'sacubitril', 'entresto'}),
        ('enalapril', {'enalapril', 'vasotec', 'epaned', 'vaseretic'})):
        if words & aliases:
            families.add(family)
    if len(families) != 1:
        return 'conflicting_names_review'
    # Known combination signals are quarantined; this does not certify no other combinations.
    if words & {'hydrochlorothiazide', 'hctz', 'chlorthalidone', 'amlodipine', 'felodipine', 'vaseretic'}:
        return 'combination_review'
    if 'valsartan' in words and 'arni' not in families:
        return 'combination_review'
    if not words & GENERIC:
        return 'brand_only_review'
    if 'metoprolol' in families:
        tartrate, succinate = 'tartrate' in words, 'succinate' in words
        if (tartrate and succinate) or (tartrate and ('toprol' in words or words & {'er', 'xr', 'xl', 'extended'})) or (succinate and 'lopressor' in words):
            return 'conflicting_names_review'
        if tartrate:
            return 'metoprolol_tartrate_candidate'
        if succinate:
            return 'metoprolol_succinate_review'
        return 'metoprolol_unspecified_review'
    if 'carvedilol' in families:
        if words & {'er', 'xr', 'cr', 'extended', 'phosphate', 'coregcr'}:
            return 'carvedilol_extended_review'
        return 'carvedilol_not_marked_extended_candidate'
    if 'arni' in families:
        return 'sacubitril_valsartan_candidate' if {'sacubitril', 'valsartan'} <= words else 'sacubitril_without_valsartan_review'
    return 'enalapril_candidate'


def run(root, relative, output, schema, max_rows=500000, catalog_limit=2000):
    root, output = Path(root), Path(output)
    if not root.is_absolute() or not output.is_absolute() or not schema:
        raise ValueError('explicit_paths_and_schema_required')
    root, output = root.resolve(), output.resolve()
    if output == root or root in output.parents or output in root.parents:
        raise ValueError('output_must_be_separate')
    if (max_rows is not None and max_rows <= 0) or catalog_limit <= 0:
        raise ValueError('invalid_limit')
    os.umask(0o077)
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    report = {'version': 1, 'status': 'running', 'restricted_until_reviewed': True,
        'source': str(root / relative), 'max_rows': max_rows, 'mapping_version': 'hf_name_screen_v1',
        'parser': 'provisional_literal_tabs_1MiB_no_skips',
        'interpretation': 'Lexical candidates only; no drug map, HF eligibility, new use, dispensing or adherence validated.',
        'candidate_stratum': 'ORDERING_MODE=Outpatient and ORDER_CLASS in Normal/Print, case-insensitive; exploratory, not an inclusion rule; no status exclusion',
        'patient_key_policy': 'trimmed exact keys; blank/candidate-null markers excluded; no numeric normalization or linkage validation',
        'route_policy': 'No route exclusion; review raw route and formulation categories before arm qualification',
        'eligible_HF_patients': None, 'verified_fill_patients': None}
    save(output / 'summary.json', report)
    rows = hits = missing_names = missing_patient = 0
    counters = {b: Counter(dict.fromkeys(('records', 'outpatient_normal_print_records',
        'outpatient_normal_print_with_parseable_order_records',
        'records_without_nonmarker_patient_key'), 0)) for b in BUCKETS}
    comparisons = {b: Counter() for b in BUCKETS}
    format_counts = {b: {'order': Counter(), 'start': Counter()} for b in BUCKETS}
    catalog, strata = Counter(), Counter()
    omitted = Counter()
    connection = None
    classify.cache_clear()
    try:
        h = inspect(root, relative)
        if h.get('status') != 'header_candidate':
            raise CountError('invalid_header_or_source')
        if h['schema_sha256'] != schema:
            raise CountError('schema_hash_mismatch')
        if h['delimiter'] != 'tab':
            raise CountError('literal_tabs_requires_tab_header')
        ix = {n: i for i, n in enumerate(h['columns'])}
        required = set(NAMES) | {'PAT_MRN_ID', 'ORDER_INST', 'START_DATE', 'ORDERING_MODE', 'ORDER_CLASS', 'MEDICATION_ID', 'MEDICATION_ROUTE'}
        if not required <= ix.keys():
            report['missing_required_fields'] = sorted(required - ix.keys())
            raise ValueError('required_fields_absent')
        source = root / relative
        before = source.stat()
        eof = False
        with tempfile.TemporaryDirectory(prefix='private-hf-', dir=output) as tmp:
            connection = sqlite3.connect(str(Path(tmp) / 'counts.sqlite'))
            connection.execute('PRAGMA temp_store=MEMORY')
            connection.execute('''CREATE TABLE people(bucket TEXT, patient TEXT, candidate INTEGER, dated INTEGER,
                first_any TEXT, first_candidate TEXT, PRIMARY KEY(bucket,patient)) WITHOUT ROWID''')
            connection.execute('CREATE TABLE dates(bucket TEXT, patient TEXT, day TEXT, PRIMARY KEY(bucket,patient,day)) WITHOUT ROWID')
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
                    if rows % 100000 == 0:
                        connection.commit()
                        print('HF screen records: ' + str(rows), flush=True)
                    def get(name):
                        return row[ix[name]].strip()
                    names = tuple(get(n) for n in NAMES)
                    if any(len(n) > 4096 for n in names):
                        raise ValueError('name_cell_exceeds_limit')
                    if all(missing_kind(v) for v in names):
                        missing_names += 1
                    bucket = classify(names)
                    if bucket is None:
                        continue
                    hits += 1
                    mode, cls, route = get('ORDERING_MODE'), get('ORDER_CLASS'), get('MEDICATION_ROUTE')
                    candidate = mode.casefold() == 'outpatient' and cls.casefold() in {'normal', 'print'}
                    order_label, order = parse(get('ORDER_INST'))
                    start_label, start = parse(get('START_DATE'))
                    c = counters[bucket]
                    c['records'] += 1
                    c['outpatient_normal_print_records'] += candidate
                    c['outpatient_normal_print_with_parseable_order_records'] += candidate and order is not None
                    comparisons[bucket][compare(order, start)] += 1
                    format_counts[bucket]['order'][order_label] += 1
                    format_counts[bucket]['start'][start_label] += 1
                    key = (bucket, mode, cls, route)
                    if key in strata or len(strata) < catalog_limit:
                        strata[key] += 1
                    else:
                        omitted['strata_records'] += 1
                    key = (bucket, get('MEDICATION_ID'), *names, route)
                    if key in catalog or len(catalog) < catalog_limit:
                        catalog[key] += 1
                    else:
                        omitted['name_catalog_records'] += 1
                    patient = get('PAT_MRN_ID')
                    if missing_kind(patient):
                        missing_patient += 1
                        c['records_without_nonmarker_patient_key'] += 1
                        continue
                    day = order.isoformat() if order else None
                    connection.execute('''INSERT INTO people VALUES(?,?,?,?,?,?) ON CONFLICT(bucket,patient)
                        DO UPDATE SET candidate=MAX(candidate,excluded.candidate), dated=MAX(dated,excluded.dated),
                        first_any=CASE WHEN first_any IS NULL THEN excluded.first_any
                            WHEN excluded.first_any IS NULL THEN first_any ELSE MIN(first_any,excluded.first_any) END,
                        first_candidate=CASE WHEN first_candidate IS NULL THEN excluded.first_candidate
                            WHEN excluded.first_candidate IS NULL THEN first_candidate ELSE MIN(first_candidate,excluded.first_candidate) END''',
                        (bucket, patient, int(candidate), int(candidate and order is not None), day, day if candidate else None))
                    if candidate and day:
                        connection.execute('INSERT OR IGNORE INTO dates VALUES (?,?,?)', (bucket, patient, day))
            after = source.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise CountError('source_changed')
            patient_counts = {}
            for b in BUCKETS:
                n = connection.execute('''SELECT COUNT(*),COALESCE(SUM(candidate),0),COALESCE(SUM(dated),0),
                    COALESCE(SUM(first_any < first_candidate),0) FROM people WHERE bucket=?''', (b,)).fetchone()
                patient_counts[b] = dict(zip(('distinct_nonmarker_patient_keys', 'outpatient_normal_print_patient_keys',
                    'outpatient_normal_print_with_parseable_order_patient_keys',
                    'patients_with_earlier_recorded_same_bucket_order_than_first_candidate'), n))
            pairs = {}
            for name, (a, b) in PAIR_ARMS.items():
                overlap = connection.execute('''SELECT COUNT(*) FROM people a JOIN people b ON a.patient=b.patient
                    WHERE a.bucket=? AND b.bucket=? AND a.dated=1 AND b.dated=1''', (a, b)).fetchone()[0]
                same_day = connection.execute('''SELECT COUNT(DISTINCT a.patient) FROM dates a JOIN dates b
                    ON a.patient=b.patient AND a.day=b.day WHERE a.bucket=? AND b.bucket=?''', (a, b)).fetchone()[0]
                pairs[name] = {'candidate_buckets': [a,b], 'patients_in_both_dated_candidate_buckets': overlap,
                    'patients_with_same_calendar_day_candidate_orders_in_both': same_day}
            connection.close()
            connection = None
        restricted = {'restricted_keep_on_cluster': True,
            'mapping_review_required': True, 'catalog_limit': catalog_limit,
            'name_fields': ['bucket', 'MEDICATION_ID', *NAMES, 'MEDICATION_ROUTE'],
            'name_catalog': [{'values': list(k), 'records': v} for k,v in catalog.items()],
            'stratum_fields': ['bucket','ORDERING_MODE','ORDER_CLASS','MEDICATION_ROUTE'],
            'strata': [{'values':list(k), 'records':v} for k,v in strata.items()],
            'omitted_records': dict(omitted)}
        save(output / 'restricted_mapping_review.json', restricted)
        report.update(status='complete_file' if eof else 'bounded_prefix', reached_eof=eof,
            rows_read=rows, lexical_candidate_records=hits, rows_without_target_name_match=rows-hits,
            rows_with_all_name_fields_blank_or_candidate_markers=missing_names,
            lexical_candidate_records_without_nonmarker_patient_key=missing_patient,
            source_changed=False, source_bytes=before.st_size, source_mtime_ns=before.st_mtime_ns,
            schema_sha256=h['schema_sha256'], catalog_omitted_records=dict(omitted),
            candidates={b: {'records': counters[b]['records'], **dict(counters[b]), **patient_counts[b],
                'date_comparison_records':dict(comparisons[b]), 'date_formats':format_counts[b]} for b in BUCKETS},
            pair_overlap=pairs,
            history_interpretation='Earlier recorded same-name-bucket order only; not baseline observability, washout, first use or adherence. No cross-formulation history reconciliation.',
            count_interpretation='Patients overlap across buckets; candidate strata are exploratory. No route filter, status filter, dose requirement or HF diagnosis applied.')
    except Exception as exc:
        if connection is not None:
            connection.close()
        report.update(status='failed_counts_invalid', error_type=type(exc).__name__,
                      reason=(str(exc) if type(exc) is ValueError and str(exc) in
                              {'required_fields_absent', 'name_cell_exceeds_limit'} else failure_reason(exc)),
                      diagnostic_records_processed=rows)
    finally:
        classify.cache_clear()
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
        r = run(a.root,a.file,a.output_dir,a.expected_schema_sha256,None if a.full_scan else a.max_rows)
    except Exception as exc:
        print('Could not start: ' + type(exc).__name__)
        return 1
    print('Finished: ' + r['status'] + '. Review reports on H100.')
    return 0 if r['status'] in {'complete_file','bounded_prefix'} else 1


if __name__ == '__main__':
    raise SystemExit(main())
