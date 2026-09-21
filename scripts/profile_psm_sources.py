#!/usr/bin/env python3
"""Bounded RBC source-format/measurement reconnaissance. No clinical extraction."""
import argparse
from collections import Counter
from functools import lru_cache
import os
from pathlib import Path
import re
from time import monotonic

from inspect_psm_source_headers import FILES
from inspect_jdat_headers import inspect
from audit_medication_dates import parse
from medication_quality import missing_kind, number_kind
from count_medication_evidence import save, CountError, failure_reason
from profile_jdat_mapping import BoundedLines

SCHEMAS = {
 'patients':'ecbfa43a15e309ed30fcc696629d99330bd8ff09f3f4562f80954320199fa40c',
 'hospital_encounters':'501735e664a9bae549fdf5d5df6e695d94b225aadf98eb4eb6329ffc03c8f1f2',
 'outpatient_encounters':'744e30f62eec7987143b86c12ca80693b1f9c42a19e370bc1e21b72d9cf1258c',
 'vitals':'d363d117b7443d5957eed8c72ff8f734d7c10ae82d8a80c814c4a6093cfdfc2e',
 'labs_2025':'cdb32a17c00ec93b8d6b7a9d294c3c249c7c8274f6340381c020153763ed85ab',
 'labs_2026':'947c3bda4664542d22bf86e8b308c372575f09c0719ea108efb78dc61e2f0ce3'}
DATES={'BIRTH_DATE','DEATH_DATE','HOSP_ADMSN_DATE','HOSP_DISCH_DATE','HOSP_ADMSN_TIME',
 'HOSP_DISCH_TIME','CONTACT_DATE','APPT_MADE_DATE','ADT_ARRIVAL_TIME','EMER_ADM_TIME',
 'ED_DEPARTURE_TIME','OP_ADM_TIME','INP_ADM_TIME','RECORDED_TIME','LAB_DATE','LAB_TIME',
 'ORDERING_DATE','ORDER_INST','SPECIMN_TAKEN_DATE','SPECIMN_TAKEN_TIME','RESULT_DATE','RESULT_TIME'}
NUMBERS={'AGE_AT_ADMISSION','LOS_MINUTES','LOS_HOURS','INP_LOS_MINUTES','INP_LOS_HOURS','MEAS_VALUE','ORD_VALUE','ORD_NUM_VALUE'}
UNITS={'UNIT','UNITS','RESULT_UNIT','RESULT_UNITS','REFERENCE_UNIT'}


def domain(path):
    if path.endswith('_Patients.txt'):return 'patients'
    if '_Flo_Vitals' in path:return 'vitals'
    if '_Labs' in path:return 'labs_2025' if path.startswith('Data-2025') else 'labs_2026'
    return 'hospital_encounters' if path.endswith('_Hosp_Enc.txt') else 'outpatient_encounters'


def sources():
    return [(p,domain(p),SCHEMAS[domain(p)]) for p in FILES if p!='Data-2026-04-15/CarDS_2435227_Patients.txt']


@lru_cache(maxsize=16384)
def date_kind(value):return parse(value)[0]


def numeric_kind(value):
    result=number_kind(value)
    if result=='unrecognized_numeric_format':
        if re.fullmatch(r'\s*\d+(?:\.\d+)?\s*/\s*\d+(?:\.\d+)?\s*',value):return 'two_numbers_slash_no_interpretation'
        if re.fullmatch(r'\s*[<>]=?\s*[+-]?\d+(?:\.\d+)?\s*',value):return 'qualified_number_no_conversion'
    return result


def profile(root, relative, kind, expected, limit, catalog_limit=2000):
    started=monotonic();accepted=0
    result=dict(relative_path=relative,domain=kind,counts_valid=False,selection='bounded_prefix_requested',max_rows=limit)
    catalog=Counter();omitted=0
    try:
        h=inspect(root,relative)
        if h.get('status')!='header_candidate' or h.get('delimiter')!='tab':raise CountError('invalid_header_or_source')
        if h['schema_sha256']!=expected:raise CountError('schema_hash_mismatch')
        cols=h['columns'];path=root/relative;before=path.stat()
        dates={c:Counter() for c in cols if c in DATES};numbers={c:Counter() for c in cols if c in NUMBERS}
        units={c:Counter() for c in cols if c in UNITS};keys=Counter();eof=False
        catalog_fields=([c for c in ('COMPONENT_ID','COMPONENT_NAME','BASE_NAME') if c in cols]
                        if kind.startswith('labs') else [c for c in ('FLO_MEAS_ID','FLO_MEAS_NAME','DISP_NAME','UNIT') if c in cols] if kind=='vitals' else [])
        with path.open('rb') as f:
            f.readline(65537);lines=BoundedLines(f,'utf-8',1048576)
            while accepted<limit:
                lines.used=0
                try:line=next(lines)
                except StopIteration:eof=True;break
                payload=line[:-2] if line.endswith('\r\n') else line[:-1] if line.endswith('\n') else line
                cells=payload.split('\t')
                if len(cells)!=len(cols):raise CountError('row_width_mismatch')
                row=dict(zip(cols,cells));accepted+=1
                keys[missing_kind(row['PAT_MRN_ID']) or 'nonempty_unvalidated']+=1
                for c,counts in dates.items():
                    value=row[c];counts[date_kind(value) if len(value)<=128 else parse(value)[0]]+=1
                for c,counts in numbers.items():counts[numeric_kind(row[c])]+=1
                for c,counts in units.items():counts[missing_kind(row[c]) or 'nonempty_unvalidated']+=1
                if catalog_fields:
                    values=tuple(row[c] for c in catalog_fields)
                    if any(len(v)>256 for v in values):omitted+=1
                    elif values in catalog or len(catalog)<catalog_limit:catalog[values]+=1
                    else:omitted+=1
        after=path.stat()
        if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise CountError('source_changed')
        result.update(status='complete_file' if eof else 'bounded_prefix',counts_valid=True,
            rows_read=accepted,reached_eof=eof,schema_sha256=expected,source_changed=False,
            source_bytes=after.st_size,source_mtime_ns=after.st_mtime_ns,patient_key_presence=keys,
            date_formats=dates,numeric_formats=numbers,unit_fields_present=list(units),unit_presence=units,
            catalog_combinations_retained=len(catalog),catalog_records_omitted=omitted,
            elapsed_seconds=round(monotonic()-started,3))
        restricted=dict(relative_path=relative,fields=catalog_fields,records_omitted=omitted,
            groups=[dict(values=dict(zip(catalog_fields,k)),records=v) for k,v in sorted(catalog.items())])
        return result,restricted
    except Exception as exc:
        result.update(status='failed_counts_invalid',error_type=type(exc).__name__,reason=failure_reason(exc),
                      diagnostic_rows_before_failure=accepted)
        return result,None
    finally:date_kind.cache_clear()


def run(root,output,limit=10000,selected=None):
    root,output=Path(root),Path(output)
    if not root.is_absolute() or not output.is_absolute() or not 1<=limit<=100000:raise ValueError('explicit_paths_and_bounded_limit_required')
    root,output=root.resolve(),output.resolve()
    if root==output or root in output.parents or output in root.parents:raise ValueError('output_source_overlap')
    os.umask(0o077);output.mkdir(parents=True,exist_ok=False,mode=0o700)
    summary=dict(version=1,status='running',restricted_until_reviewed=True,files=[],max_rows_per_file=limit,
        interpretation='Nonrandom prefixes only; not patient N, clinical missingness, units validation or shared-table promotion. Deliveries remain separate.',
        parser='provisional literal tabs, 1MiB physical line limit, no skips/repairs')
    restricted=dict(restricted_keep_on_cluster=True,warning='Catalog values may contain unexpected sensitive text; review locally; do not paste wholesale.',files=[])
    save(output/'summary.json',summary)
    for i,(relative,kind,schema) in enumerate(sources() if selected is None else selected,1):
        print('Profiling source '+str(i),flush=True)
        report,catalog=profile(root,relative,kind,schema,limit)
        summary['files'].append(report)
        if catalog is not None:restricted['files'].append(catalog)
        save(output/'summary.json',summary);save(output/'restricted_measurement_catalog.json',restricted)
        print('Source '+str(i)+': '+report['status'],flush=True)
    summary['status']='complete_requested_scope' if all(f['counts_valid'] for f in summary['files']) else 'incomplete_review_failures'
    save(output/'summary.json',summary)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--max-rows-per-file',type=int,default=10000)
    a=p.parse_args()
    try:r=run(a.root,a.output_dir,a.max_rows_per_file)
    except Exception as exc:print('Could not start: '+type(exc).__name__);return 1
    print('Finished: '+r['status']+'. Review summary.json on H100.')
    return 0 if r['status']=='complete_requested_scope' else 1

if __name__=='__main__':raise SystemExit(main())
