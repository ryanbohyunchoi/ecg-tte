#!/usr/bin/env python3
"""Expanded lexical beta-blocker history and restricted mapping review; no index changes."""
import argparse
from collections import Counter
from functools import lru_cache
import json
import os
from pathlib import Path
import re
import time

from build_shared_tables import BuildError, atomic_json, digest, open_table
from build_comet_candidates import records, NAMES

# WHO ATC C07AA/C07AB/C07AG generic-name leads, checked 2026-09-21.
# This is not a medication-ID map, route policy or exhaustive historical vocabulary.
GENERICS=set('alprenolol oxprenolol pindolol propranolol timolol sotalol nadolol mepindolol carteolol tertatolol bopindolol bupranolol penbutolol cloranolol practolol metoprolol atenolol acebutolol betaxolol bevantolol bisoprolol celiprolol esmolol epanolol nebivolol talinolol landiolol labetalol carvedilol'.split())
REVIEW_BRANDS=set('coreg coregcr lopressor toprol tenormin tenoretic zebeta ziac inderal innopran bystolic normodyne trandate corgard corzide betapace sorine sotalize brevibloc sectral visken blocadren timoptic combigan cosopt'.split())


@lru_cache(maxsize=20000)
def classify(names):
    words=set(re.findall('[a-z]+',' '.join(names).lower()))
    generic=words&GENERICS
    if generic:return 'named_generic',tuple(sorted(generic))
    if words&REVIEW_BRANDS or any(w.endswith('olol') for w in words):return 'unresolved_name_lead',()
    return 'no_name_match',()


def relation(day,index):
    if day is None:return 'undated'
    lag=(index-day).days
    return 'prior365' if 1<=lag<=365 else 'same_day' if lag==0 else 'outside_window'


def verify(report):
    import pyarrow.parquet as pq
    if report.is_symlink():raise BuildError('symlink_report')
    s=json.loads((report/'summary.json').read_text());m=json.loads((report/'restricted_manifest.json').read_text())
    p=report/'restricted_broad_candidates.parquet'
    if s.get('version')!='comet_broad_exploratory_v2' or m.get('version')!=s['version'] or s.get('status')!='complete_exploratory_cohort_audit' or s.get('counts_valid') is not True:raise BuildError('need_completed_excluded_v2_cohort')
    if p.is_symlink() or digest(p)!=m.get('output_sha256'):raise BuildError('cohort_hash_mismatch')
    with pq.ParquetFile(p) as f:
        if f.metadata.num_rows!=s['selected_candidate_keys'] or f.metadata.num_rows!=m['rows']:raise BuildError('cohort_rows_mismatch')
    core=Path(s['core_snapshot'])
    if digest(core/'manifest.json')!=m['core_manifest_sha256']:raise BuildError('core_manifest_changed')
    return s,m


def discover(root):
    found=[]
    for run in sorted(Path(root).glob('comet-broad-*')):
        try:verify(run/'report')
        except (BuildError,FileNotFoundError):continue
        found.append(run/'report')
    if len(found)!=1:raise BuildError('need_one_verified_v2_cohort_or_explicit_report')
    return found[0]


def run(cohort_report,output):
    import pyarrow.parquet as pq
    cohort_report,output=Path(cohort_report),Path(output)
    if not cohort_report.is_absolute() or not output.is_absolute() or output.is_symlink():raise BuildError('absolute_paths_required')
    s,m=verify(cohort_report);core=Path(s['core_snapshot'])
    for source in (core.resolve(),cohort_report.resolve()):
        if output.resolve()==source or source in output.resolve().parents or output.resolve() in source.parents:raise BuildError('output_source_overlap')
    started=time.monotonic();os.umask(0o077);output.mkdir(parents=True,exist_ok=False,mode=0o700)
    summary=dict(version='comet_beta_history_v1',status='building',counts_valid=False,restricted_until_reviewed=True,
        interpretation='Expanded generic/brand lexical screen only; all routes/classes retained. No validated class washout, eligibility exclusion, reindexing or PSM.',
        rules='Strict prior days1-365; undated and same-day separate. Future/older non-index records not catalogued. No name match does not prove no beta-blocker.',
        cohort_report=str(cohort_report),cohort_sha256=m['output_sha256'],script_sha256=digest(Path(__file__)),
        qualified_new_user_patients=None)
    atomic_json(output/'summary.json',summary)
    try:
        cohort=pq.read_table(cohort_report/'restricted_broad_candidates.parquet',columns=['patient_key','candidate_arm','candidate_order_day','candidate_order_source_rows']).to_pylist()
        anchors={r['patient_key']:r for r in cohort}
        if len(anchors)!=len(cohort):raise BuildError('duplicate_cohort_key')
        expected={}
        for r in cohort:
            if not r['patient_key'] or r['candidate_order_day'] is None or not r['candidate_order_source_rows']:
                raise BuildError('invalid_candidate_anchor')
            for ordinal in r['candidate_order_source_rows']:
                if type(ordinal) is not int or ordinal<1:raise BuildError('invalid_index_lineage')
                if ordinal in expected:raise BuildError('duplicate_index_lineage')
                expected[ordinal]=r['patient_key']
        found=set();flags={p:set() for p in anchors};catalog=Counter();matched=Counter()
        table=open_table(core,'medication_orders');stamps={p:(Path(p).stat().st_size,Path(p).stat().st_mtime_ns) for p in table.files}
        cols=['__patient_key','__source_row','__day_ORDER_INST','MEDICATION_ID','MEDICATION_ROUTE','ORDERING_MODE','ORDER_CLASS',*NAMES]
        for row in records(table,cols):
            ordinal=row['__source_row'];key=row['__patient_key']
            if ordinal in expected and expected[ordinal]!=key:raise BuildError('index_patient_lineage_mismatch')
            if key not in anchors:continue
            day=row['__day_ORDER_INST'];anchor=anchors[key]
            is_index=ordinal in expected
            if is_index:
                if day!=anchor['candidate_order_day']:raise BuildError('index_date_lineage_mismatch')
                found.add(ordinal)
            timing='index' if is_index else relation(day,anchor['candidate_order_day'])
            if timing=='outside_window':continue
            names=tuple(row[n] or '' for n in NAMES)
            if any(len(n)>4096 for n in names):raise BuildError('oversized_medication_name')
            label,ingredients=classify(names)
            if label=='no_name_match' and not is_index:continue
            if timing in ('prior365','undated','same_day'):
                flags[key].add(timing+'_'+label)
            matched[anchor['candidate_arm'],timing,label]+=1
            values=(timing,label,','.join(ingredients),*(row[n] or '' for n in ('MEDICATION_ID',*NAMES,'MEDICATION_ROUTE','ORDERING_MODE','ORDER_CLASS')))
            if any(len(v)>4096 for v in values):raise BuildError('oversized_catalog_field')
            if values not in catalog and len(catalog)>=20000:raise BuildError('catalog_limit_no_silent_omission')
            catalog[values]+=1
        if found!=set(expected):raise BuildError('index_source_rows_missing')
        if digest(cohort_report/'restricted_broad_candidates.parquet')!=m['output_sha256'] or digest(core/'manifest.json')!=m['core_manifest_sha256'] or any((Path(p).stat().st_size,Path(p).stat().st_mtime_ns)!=stamp for p,stamp in stamps.items()):raise BuildError('input_changed')
        groups=Counter();denominators=Counter()
        for p,row in anchors.items():
            f=flags[p];arm=row['candidate_arm'];denominators[arm]+=1
            groups[arm,'prior365_named_generic' in f,'undated_named_generic' in f,
                   bool(f&{'prior365_unresolved_name_lead','undated_unresolved_name_lead'}),
                   bool(f&{'same_day_named_generic','same_day_unresolved_name_lead'})]+=1
        fields=['timing','lexical_status','generic_leads','MEDICATION_ID',*NAMES,'MEDICATION_ROUTE','ORDERING_MODE','ORDER_CLASS']
        atomic_json(output/'restricted_medication_mapping.json',dict(restricted_keep_on_cluster=True,
            warning='Review locally; unexpected source text may be sensitive. No medication mapping is approved by this file.',
            fields=fields,groups=[dict(values=dict(zip(fields,k)),records=n) for k,n in sorted(catalog.items())]))
        summary.update(status='complete_history_screen',counts_valid=True,denominators=dict(denominators),
            index_rows_verified=len(found),catalog_combinations=len(catalog),
            history_groups=[dict(arm=a,prior365_generic_found=p,undated_generic_found=u,
                unresolved_prior_or_undated_lead=l,other_same_day_lead=t,patient_keys=n) for (a,p,u,l,t),n in sorted(groups.items())],
            record_counts=[dict(arm=a,timing=t,lexical_status=l,records=n) for (a,t,l),n in sorted(matched.items())])
    except Exception as exc:
        summary.update(status='failed_counts_invalid',counts_valid=False,reason=str(exc) if isinstance(exc,BuildError) else 'audit_failed_no_raw_error_export')
        raise
    finally:
        classify.cache_clear();summary['elapsed_seconds']=round(time.monotonic()-started,3);atomic_json(output/'summary.json',summary)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--cohort-report',type=Path);g.add_argument('--audit-root',type=Path)
    p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    try:r=run(a.cohort_report or discover(a.audit_root),a.output_dir)
    except Exception as exc:
        print('Stopped: '+(str(exc) if isinstance(exc,BuildError) else type(exc).__name__));return 1
    print('Finished: '+r['status']+'. Review summary.json on H100.');return 0

if __name__=='__main__':raise SystemExit(main())
