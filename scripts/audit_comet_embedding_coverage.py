#!/usr/bin/env python3
"""Aggregate-only linkage feasibility; no vectors, notes, or matching are loaded."""
import argparse
from collections import Counter, defaultdict
from datetime import date, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import time
import pyarrow.parquet as pq
from build_shared_tables import atomic_json
from inspect_embedding_assets import LEADS

ALIASES = ('FileID', 'fileID')


def key(value):
    if value is None: return None
    value = str(value).strip()
    return None if value.upper() in ('', 'NULL', 'NAN', 'NONE', 'NA') else value


def day(value):
    if isinstance(value, datetime):
        return value.date() if value.tzinfo is None else None
    if isinstance(value, date): return value
    value = key(value)
    if not value or not re.fullmatch(r'\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?)?', value): return None
    try: return datetime.fromisoformat(value).date()
    except ValueError: return None


def stamp(path):
    s = path.stat()
    return [s.st_size, s.st_mtime_ns]


def records(path, columns):
    for batch in pq.ParquetFile(path).iter_batches(batch_size=65536, columns=columns):
        yield from batch.to_pylist()


def audit(roster, metadata, caches, vector_dir):
    people = {}
    for r in roster:
        p, d = key(r['patient_key']), day(r['index_date'])
        if not p or not d or p in people: raise ValueError('invalid_or_duplicate_roster')
        people[p] = (r['treatment_arm'], d)
    if not people: raise ValueError('empty_roster')
    if not vector_dir.is_dir(): raise ValueError('vector_directory_missing')
    sources = [metadata, *caches.values()]
    before = {str(p): stamp(p) for p in sources}
    cache_counts = {name: Counter(key(r['file_id']) for r in records(p, ['file_id'])) for name,p in caches.items()}
    candidates = []
    relevant = set()
    qc = Counter()
    for r in records(metadata, ['MRN','ECGDate',*ALIASES]):
        qc['metadata_rows'] += 1
        p = key(r['MRN'])
        if p not in people: continue
        qc['cohort_metadata_rows'] += 1
        d = day(r['ECGDate'])
        if d is None:
            qc['cohort_unparsed_date_rows'] += 1
            continue
        lag = (people[p][1] - d).days
        if lag == 0: qc['cohort_same_day_rows'] += 1
        if not 1 <= lag <= 365: continue
        ids = [key(r[a]) for a in ALIASES]
        qc['preindex_alias_equal_rows' if ids[0] == ids[1] else 'preindex_alias_different_rows'] += 1
        for alias, fid in zip(ALIASES, ids):
            if fid:
                candidates.append((p,d,alias,fid))
                relevant.add(fid)
    # Second projected pass detects collisions even outside the cohort and across aliases.
    owners = {}
    ambiguous = set()
    for r in records(metadata, ['MRN','ECGDate',*ALIASES]):
        for fid in {key(r[a]) for a in ALIASES} & relevant:
            identity = (key(r['MRN']), day(r['ECGDate']))
            if None in identity or (fid in owners and owners[fid] != identity): ambiguous.add(fid)
            owners[fid] = identity
    coverage = defaultdict(set)
    existence = {}
    for p,d,alias,fid in candidates:
        arm = people[p][0]
        coverage[(arm,alias,'preindex_metadata')].add(p)
        if fid in ambiguous: continue
        coverage[(arm,alias,'unambiguous_preindex_metadata')].add(p)
        safe = fid not in ('.','..') and '/' not in fid and '\\' not in fid and '\x00' not in fid
        if fid not in existence:
            path = vector_dir / (fid + '.npy') if safe else None
            existence[fid] = bool(path and not path.is_symlink() and path.is_file() and path.stat().st_size > 0)
        ecg = existence[fid]
        if ecg: coverage[(arm,alias,'ecg_vector_file_present')].add(p)
        for name, counts in cache_counts.items():
            if counts[fid] == 1:
                coverage[(arm,alias,name)].add(p)
                if ecg: coverage[(arm,alias,'same_ecg_file_and_' + name)].add(p)
    if any(stamp(p) != before[str(p)] for p in sources): raise ValueError('source_changed')
    arms = Counter(a for a,d in people.values())
    evidence = ['preindex_metadata','unambiguous_preindex_metadata','ecg_vector_file_present',*caches,*('same_ecg_file_and_'+n for n in caches)]
    return dict(denominators=dict(arms), qc=dict(qc), ambiguous_candidate_file_ids=len(ambiguous),
                sources=before, cache_qc={n:dict(rows=sum(c.values()),missing_file_id_rows=c[None],duplicate_nonempty_file_ids=sum(v>1 for k,v in c.items() if k)) for n,c in cache_counts.items()},
                coverage=[dict(arm=a,metadata_alias=alias,evidence=e,patients=len(coverage[(a,alias,e)])) for a in sorted(arms) for alias in ALIASES for e in evidence])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-report',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    if not args.source_report.is_absolute() or not args.output_dir.is_absolute(): parser.error('absolute paths required')
    os.umask(0o077)
    args.output_dir.mkdir(parents=True,exist_ok=False,mode=0o700)
    result=dict(version='comet_embedding_coverage_v1',status='running',counts_valid=False,restricted_until_reviewed=True,ready_for_matching=False,
                interpretation='Feasibility only: exact trimmed keys, aliases evaluated separately, strictly prior calendar days 1-365. No vector validation, chosen ECG, CLMBR history-cutoff verification, model provenance approval or matching. Counts overlap; do not sum aliases/caches.')
    atomic_json(args.output_dir/'summary.json',result)
    start=time.monotonic()
    try:
        src=args.source_report
        s=json.loads((src/'summary.json').read_text())
        m=json.loads((src/'manifest.json').read_text())
        name='restricted_cleaned_baseline.parquet'
        baseline=src/name
        if s.get('status')!='complete_mice_preparation' or s.get('counts_valid') is not True: raise ValueError('complete_preparation_required')
        digest=hashlib.sha256(baseline.read_bytes()).hexdigest()
        if m['outputs'].get(name)!=digest: raise ValueError('baseline_hash_mismatch')
        roster=list(records(baseline,['patient_key','treatment_arm','index_date']))
        if len(roster)!=s['rows'] or dict(Counter(r['treatment_arm'] for r in roster))!=s['denominators']: raise ValueError('roster_mismatch')
        result.update(audit(roster,Path(LEADS['ecg_metadata']),{n:Path(LEADS[n]) for n in ('clmbr_allcomers_cache','clmbr_v2_train_cache')},Path(LEADS['legacy_comet_ecg_embeddings'])))
        result.update(status='complete_linkage_feasibility',counts_valid=True,baseline_sha256=digest)
    except Exception as exc:
        # Never emit exception text: libraries may include identifiers or record content.
        result.update(status='failed_coverage',counts_valid=False,error_type=type(exc).__name__)
    result['elapsed_seconds']=round(time.monotonic()-start,3)
    atomic_json(args.output_dir/'summary.json',result)
    print('Finished:',result['status'],'— review summary.json locally.')
    return 0 if result['counts_valid'] else 1

if __name__=='__main__': raise SystemExit(main())
