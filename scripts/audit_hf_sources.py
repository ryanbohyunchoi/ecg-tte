#!/usr/bin/env python3
"""Provisional HF source QC and exact-key coverage, not eligibility or initiation."""
import argparse
from collections import Counter
import math
from datetime import date
from pathlib import Path
import os
import re
import sqlite3
import tempfile

from audit_hf_medications import classify, NAMES, PAIR_ARMS
from audit_medication_dates import parse, compare, shape
from count_medication_evidence import CountError, failure_reason, save
from inspect_jdat_headers import inspect
from medication_quality import missing_kind
from profile_jdat_mapping import BoundedLines

MED_SCHEMA = '61f9556c4f054c3346d46f78e63d65a467e022f800fb0b388e5dbcf622903da8'
DX_SCHEMA = 'eee6c9922b68b8f5c95022eff2a9c7b827478195d07167c62343060cb7e75cb4'
ARMS = tuple(dict.fromkeys(b for pair in PAIR_ARMS.values() for b in pair))
DX_DATES = ('CALC_DX_DATE', 'DX_DTTM', 'DX_DATE')


def key(value):
    value = '' if value is None else str(value).strip()
    return None if missing_kind(value) else value


def ef_band(value):
    if value is None:
        return 'null'
    if not isinstance(value, (float, int)) or isinstance(value, bool):
        return 'unexpected_type'
    if not math.isfinite(value):
        return 'nonfinite'
    if value < 0 or value > 100:
        return 'outside_0_100'
    if value == 0:
        return 'zero'
    if value <= 1:
        return 'positive_le_1_scale_ambiguous'
    if value <= 35:
        return 'gt_1_le_35'
    if value <= 40:
        return 'gt_35_le_40'
    if value <= 50:
        return 'gt_40_le_50'
    return 'gt_50_le_100'


def code_structure(value):
    if missing_kind(value):
        return 'missing'
    # Lexical structure only; does not validate codes, split lists or assign HF.
    if re.fullmatch(r'[A-Za-z][0-9][A-Za-z0-9](?:\.?[A-Za-z0-9]{1,4})?', value):
        return 'single_icd10_shaped_token'
    found = [label for char, label in [(';', 'semicolon'), (',', 'comma'), ('|', 'pipe')] if char in value]
    return 'contains_' + '_and_'.join(found) if found else 'other_structure'


def recency_band(days):
    if days is None:
        return 'no_prior_candidate_ef'
    if days <= 0:
        raise ValueError('strictly_prior_required')
    for bound in (90, 180, 365, 730):
        if days <= bound:
            return 'days_' + ('1' if bound == 90 else str({180:91,365:181,730:366}[bound])) + '_' + str(bound)
    return 'days_over_730'


def token_structure(value):
    if missing_kind(value):
        return 'missing'
    # Explicit lexical hypothesis; no vocabulary validity or HF classification.
    if len(value) > 4096:
        return 'oversized_not_tokenized'
    tokens = re.split(r'[,;|]', value)
    if any(not t.strip() for t in tokens):
        return 'empty_token_review'
    if all(code_structure(t.strip()) == 'single_icd10_shaped_token' for t in tokens):
        return 'single_shaped_token' if len(tokens) == 1 else 'all_split_tokens_code_shaped'
    return 'unresolved_tokens_review'


def calendar_report(db):
    result = {}
    for bucket in ARMS:
        years = [r[0] for r in db.execute('SELECT DISTINCT substr(day,1,4) FROM meds WHERE bucket=? ORDER BY 1',(bucket,))]
        groups = []
        for year in years:
            bands = Counter()
            latest = Counter()
            for patient, anchor in db.execute('SELECT patient,day FROM meds WHERE bucket=? AND substr(day,1,4)=?',(bucket,year)).fetchall():
                row = db.execute('SELECT lag FROM recency WHERE bucket=? AND patient=?',(bucket,patient)).fetchone()
                bands[recency_band(row[0] if row else None)] += 1
                ef_rows = db.execute('SELECT band FROM latest_echo WHERE bucket=? AND patient=?',(bucket,patient)).fetchall()
                labels = {r[0] for r in ef_rows}
                latest['no_prior_echo' if not labels else next(iter(labels)) if len(labels)==1 else 'same_latest_day_band_disagreement'] += 1
            groups.append(dict(anchor_year=year, candidate_patient_keys=sum(bands.values()),
                nearest_prior_candidate_ef_recency=dict(bands), latest_prior_echo_ef_bands=dict(latest)))
        result[bucket] = dict(first_candidate_anchor_years=groups,
            any_candidate_order_years=[dict(year=y,patient_keys=n) for y,n in db.execute(
                'SELECT year,COUNT(*) FROM med_years WHERE bucket=? GROUP BY year ORDER BY year',(bucket,))])
    return result


def literal_rows(path, schema, report, limit=None, allow_terminal_empty_line=False):
    before = path.stat()
    header = inspect(path.parent, path.name)
    if header.get('status') != 'header_candidate' or header.get('delimiter') != 'tab':
        raise CountError('invalid_header_or_source')
    if header['schema_sha256'] != schema:
        raise CountError('schema_hash_mismatch')
    report.update(rows_read=0, physical_lines_read=0, terminal_empty_lines_accepted=0,
                  terminal_empty_line_policy='one_empty_line_at_eof' if allow_terminal_empty_line else 'reject',
                  reached_eof=False, schema_sha256=schema)
    with path.open('rb') as stream:
        stream.readline(65537)
        lines = BoundedLines(stream, 'utf-8-sig', 1048576)
        while limit is None or report['rows_read'] < limit:
            lines.used = 0
            line_offset = stream.tell()
            try:
                line = next(lines)
            except StopIteration:
                report['reached_eof'] = True
                break
            report['physical_lines_read'] += 1
            if (allow_terminal_empty_line and line in ('\n', '\r\n')
                    and stream.tell() - line_offset == len(line.encode('utf-8'))):
                if stream.read(1) != b'':
                    raise CountError('row_width_mismatch')
                report['terminal_empty_lines_accepted'] = 1
                report['reached_eof'] = True
                break
            cells = line.rstrip('\r\n').split('\t')
            if len(cells) != len(header['columns']):
                raise CountError('row_width_mismatch')
            report['rows_read'] += 1
            if report['rows_read'] % 100000 == 0:
                print('Processed records: ' + str(report['rows_read']), flush=True)
            yield dict(zip(header['columns'], cells))
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise CountError('source_changed')
    report.update(source_changed=False, source_bytes=after.st_size,
                  source_mtime_ns=after.st_mtime_ns,
                  status='complete_file' if report['reached_eof'] else 'bounded_prefix')


def init_db(db):
    db.executescript('''
      PRAGMA temp_store=MEMORY;
      CREATE TABLE meds(bucket TEXT, patient TEXT, day TEXT,
        PRIMARY KEY(bucket,patient)) WITHOUT ROWID;
      CREATE INDEX med_patient ON meds(patient);
      CREATE TABLE med_years(bucket TEXT, patient TEXT, year TEXT,
        PRIMARY KEY(bucket,patient,year)) WITHOUT ROWID;
      CREATE TABLE recency(bucket TEXT, patient TEXT, lag INTEGER,
        PRIMARY KEY(bucket,patient)) WITHOUT ROWID;
      CREATE TABLE latest_echo(bucket TEXT, patient TEXT, day TEXT, band TEXT,
        PRIMARY KEY(bucket,patient,band)) WITHOUT ROWID;
      CREATE TABLE echo(patient TEXT PRIMARY KEY) WITHOUT ROWID;
      CREATE TABLE accessions(accession TEXT PRIMARY KEY, patient TEXT, day TEXT, ef TEXT) WITHOUT ROWID;
      CREATE TABLE coverage(bucket TEXT, patient TEXT, flag TEXT,
        PRIMARY KEY(bucket,patient,flag)) WITHOUT ROWID;
      CREATE TABLE dx_keys(patient TEXT PRIMARY KEY) WITHOUT ROWID;
    ''')


def echo_records(records, db, report):
    counts, dates, shapes = Counter(), Counter(), Counter()
    for row in records:
        counts['rows'] += 1
        patient = key(row['MRN'])
        raw_date = row['EchoDate'] or ''
        fmt, day = parse(raw_date)
        dates[fmt] += 1
        masked = shape(raw_date)
        if masked in shapes or len(shapes) < 100:
            shapes[masked] += 1
        else:
            counts['masked_shapes_omitted'] += 1
        band = ef_band(row['EF'])
        counts['ef_' + band] += 1
        if not patient:
            counts['missing_patient_key'] += 1
        else:
            db.execute('INSERT OR IGNORE INTO echo VALUES (?)', (patient,))
        accession = key(row['AccessionNumber'])
        if accession:
            signature = (patient, raw_date, repr(row['EF']))
            old = db.execute('SELECT patient,day,ef FROM accessions WHERE accession=?', (accession,)).fetchone()
            if old is not None:
                counts['repeated_accession_rows'] += 1
                if tuple(old) != signature:
                    counts['accession_rows_disagreeing_with_first'] += 1
            else:
                db.execute('INSERT INTO accessions VALUES (?,?,?,?)', (accession, *signature))
        else:
            counts['missing_accession'] += 1
        if patient:
            for bucket, index in db.execute('SELECT bucket,day FROM meds WHERE patient=?', (patient,)).fetchall():
                flags = ['any_echo']
                if day:
                    relation = 'before' if day.isoformat() < index else 'same_day' if day.isoformat() == index else 'after'
                    flags.append('echo_' + relation)
                    if relation == 'before':
                        old_day = db.execute('SELECT MAX(day) FROM latest_echo WHERE bucket=? AND patient=?',(bucket,patient)).fetchone()[0]
                        if old_day is None or day.isoformat() > old_day:
                            db.execute('DELETE FROM latest_echo WHERE bucket=? AND patient=?',(bucket,patient))
                            old_day = day.isoformat()
                        if day.isoformat() == old_day:
                            db.execute('INSERT OR IGNORE INTO latest_echo VALUES (?,?,?,?)',(bucket,patient,day.isoformat(),band))
                        if band.startswith('gt_'):
                            lag = (date.fromisoformat(index)-day).days
                            db.execute('INSERT INTO recency VALUES (?,?,?) ON CONFLICT(bucket,patient) DO UPDATE SET lag=MIN(lag,excluded.lag)',(bucket,patient,lag))
                    if band.startswith('gt_'):
                        flags.append('ef_gt1_le100_' + relation)
                for flag in flags:
                    db.execute('INSERT OR IGNORE INTO coverage VALUES (?,?,?)', (bucket, patient, flag))
        if counts['rows'] % 100000 == 0:
            db.commit()
            print('Echo records: ' + str(counts['rows']), flush=True)
    db.commit()
    report.update(counts=dict(counts), date_formats=dict(dates), masked_date_shapes=dict(shapes),
        distinct_nonmarker_patient_keys=db.execute('SELECT COUNT(*) FROM echo').fetchone()[0],
        distinct_nonmarker_accessions=db.execute('SELECT COUNT(*) FROM accessions').fetchone()[0])


def run(root, echo_path, output, dx_limit=500000, allow_hospital_terminal_empty_line=False):
    root, echo_path, output = map(Path, (root, echo_path, output))
    if not all(p.is_absolute() for p in (root, echo_path, output)) or (dx_limit is not None and dx_limit <= 0):
        raise ValueError('absolute_paths_and_positive_dx_limit_required')
    root, echo_path, output = root.resolve(), echo_path.resolve(), output.resolve()
    for source in (root, echo_path.parent):
        if output == source or source in output.parents or output in source.parents:
            raise ValueError('output_must_be_separate_from_sources')
    os.umask(0o077)
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    report = dict(version=3, status='running', restricted_until_reviewed=True,
        counts_valid=False, root=str(root), echo_source=str(echo_path), dx_max_rows_per_file=dx_limit,
        interpretation='QC only. No HF phenotype, validated identity, eligibility, new use, fills or adherence.',
        index='Earliest dated outpatient Normal/Print lexical order per arm; exploratory anchor only.',
        timing='Calendar days; same-day separate; no report availability timestamp; date semantics unverified.',
        ef_policy='Descriptive bands only; >1 to 100 is a candidate numeric range, not validated percent EF.',
        identity='Trimmed exact strings; null markers excluded; no prefix stripping or zero removal.',
        parser='Provisional literal tabs; 1MiB lines; no skipped rows; DX prefixes not representative.',
        hospital_terminal_empty_line_enabled=allow_hospital_terminal_empty_line,
        medications={}, echo={}, diagnoses={})
    save(output/'summary.json', report)
    stage = 'dependencies'
    try:
        import pyarrow.parquet as pq
        source_paths = [echo_path] + [root/name for name in (
            'CarDS_2435227_Meds.txt', 'CarDS_2435227_Hosp_Enc_DX.txt',
            'CarDS_2435227_Outpatient_Enc_DX.txt')]
        snapshots = {p: (p.stat().st_size, p.stat().st_mtime_ns) for p in source_paths}
        with tempfile.TemporaryDirectory(prefix='private-hf-source-', dir=output) as tmp:
            db = sqlite3.connect(str(Path(tmp)/'audit.sqlite'))
            try:
                init_db(db)
                stage = 'medications'
                for row in literal_rows(root/'CarDS_2435227_Meds.txt', MED_SCHEMA, report['medications']):
                    if any(len(row[n]) > 4096 for n in NAMES):
                        raise ValueError('oversized_name')
                    bucket = classify(tuple(row[n] for n in NAMES))
                    if bucket not in ARMS or row['ORDERING_MODE'].strip().lower() != 'outpatient' or row['ORDER_CLASS'].strip().lower() not in ('normal', 'print'):
                        continue
                    patient, day = key(row['PAT_MRN_ID']), parse(row['ORDER_INST'])[1]
                    if patient and day:
                        db.execute('INSERT OR IGNORE INTO med_years VALUES (?,?,?)',(bucket,patient,str(day.year).zfill(4)))
                        db.execute('INSERT INTO meds VALUES (?,?,?) ON CONFLICT(bucket,patient) DO UPDATE SET day=MIN(day,excluded.day)',
                                   (bucket, patient, day.isoformat()))
                db.commit()
                stage = 'echo'
                before = echo_path.stat()
                with pq.ParquetFile(echo_path) as pf:
                    columns = {'MRN':'string', 'EchoDate':'string', 'EF':'double', 'AccessionNumber':'string'}
                    actual = {f.name: str(f.type) for f in pf.schema_arrow}
                    if any(actual.get(k) != v for k,v in columns.items()):
                        raise ValueError('echo_schema_mismatch')
                    report['echo']['footer_rows'] = pf.metadata.num_rows
                    records = (row for batch in pf.iter_batches(batch_size=16384, columns=list(columns)) for row in batch.to_pylist())
                    echo_records(records, db, report['echo'])
                after = echo_path.stat()
                if (before.st_size,before.st_mtime_ns) != (after.st_size,after.st_mtime_ns):
                    raise CountError('source_changed')
                if report['echo']['counts'].get('rows',0) != report['echo']['footer_rows']:
                    raise ValueError('echo_row_count_mismatch')
                report['echo'].update(status='complete_file', source_changed=False)
                report['arm_echo_coverage'] = {}
                for bucket in ARMS:
                    report['arm_echo_coverage'][bucket] = dict(
                        candidate_patient_keys=db.execute('SELECT COUNT(*) FROM meds WHERE bucket=?',(bucket,)).fetchone()[0],
                        flags=dict(db.execute('SELECT flag,COUNT(*) FROM coverage WHERE bucket=? GROUP BY flag',(bucket,))))
                report['calendar_and_recency'] = calendar_report(db)
                for filename in ('CarDS_2435227_Hosp_Enc_DX.txt', 'CarDS_2435227_Outpatient_Enc_DX.txt'):
                    stage = filename
                    result = report['diagnoses'][filename] = {}
                    formats = {f:Counter() for f in DX_DATES}
                    comparisons = {f:Counter() for f in DX_DATES[1:]}
                    structures, missing, tokens, dx_years = Counter(), Counter(), Counter(), Counter()
                    db.execute('DELETE FROM dx_keys')
                    for row in literal_rows(root/filename, DX_SCHEMA, result, dx_limit,
                            allow_terminal_empty_line=allow_hospital_terminal_empty_line and filename == 'CarDS_2435227_Hosp_Enc_DX.txt'):
                        patient = key(row['PAT_MRN_ID'])
                        if patient:
                            db.execute('INSERT OR IGNORE INTO dx_keys VALUES (?)',(patient,))
                        else:
                            missing['missing_patient_key_rows'] += 1
                        parsed = {}
                        for field in DX_DATES:
                            fmt, parsed[field] = parse(row[field])
                            formats[field][fmt] += 1
                        for field in comparisons:
                            comparisons[field][compare(parsed['CALC_DX_DATE'],parsed[field])] += 1
                        cell = row['CURRENT_ICD10_LIST'].strip()
                        structures[code_structure(cell)] += 1
                        tokens[token_structure(cell)] += 1
                        year = str(parsed['CALC_DX_DATE'].year).zfill(4) if parsed['CALC_DX_DATE'] else 'unparseable_calc_date'
                        state = 'dx_date_present' if parsed['DX_DATE'] else 'dx_date_unusable'
                        dx_years[(year,state)] += 1
                    result.update(date_formats=formats, date_comparisons_to_CALC_DX_DATE=comparisons,
                        comparison_labels='order means CALC_DX_DATE; start means the other field; no preferred date selected',
                        icd10_cell_structure=structures, tokenization_hypothesis_counts=tokens,
                        calc_year_dx_date_availability=[dict(calc_year=y,state=k,records=n) for (y,k),n in sorted(dx_years.items())], missing=missing,
                        distinct_patient_keys_in_scanned_rows=db.execute('SELECT COUNT(*) FROM dx_keys').fetchone()[0],
                        keys_also_in_echo=db.execute('SELECT COUNT(*) FROM dx_keys JOIN echo USING(patient)').fetchone()[0],
                        medication_candidate_overlap=dict(db.execute('SELECT bucket,COUNT(*) FROM meds JOIN dx_keys USING(patient) GROUP BY bucket')))
            finally:
                db.close()
        stage = 'final_source_stability'
        if any((p.stat().st_size, p.stat().st_mtime_ns) != stamp for p,stamp in snapshots.items()):
            raise CountError('source_changed')
        report.update(status='complete_requested_scope', counts_valid=True)
    except Exception as exc:
        report = {k:v for k,v in report.items() if k not in ('medications','echo','diagnoses','arm_echo_coverage','calendar_and_recency')}
        report.update(status='failed_counts_invalid', counts_valid=False, failure_stage=stage,
                      error_type=type(exc).__name__, reason=failure_reason(exc))
    save(output/'summary.json', report)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', required=True)
    p.add_argument('--echo', required=True)
    p.add_argument('--output-dir', required=True)
    scope = p.add_mutually_exclusive_group()
    scope.add_argument('--dx-max-rows', type=int, default=500000)
    scope.add_argument('--dx-full-scan', action='store_true')
    p.add_argument('--allow-hospital-terminal-empty-line', action='store_true',
                   help='Accept and count exactly one empty final physical line in hospital DX only')
    args = p.parse_args()
    try:
        report = run(args.root,args.echo,args.output_dir,None if args.dx_full_scan else args.dx_max_rows, args.allow_hospital_terminal_empty_line)
    except Exception as exc:
        print('Setup failed: ' + type(exc).__name__)
        return 1
    print('Finished: ' + report['status'] + '. Review summary.json on H100.')
    return 0 if report['counts_valid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
