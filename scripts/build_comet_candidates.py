#!/usr/bin/env python3
"""Provisional COMET candidates from a complete core snapshot; never eligibility."""
import argparse
from collections import Counter
from datetime import timedelta
from functools import lru_cache
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import time

from build_shared_tables import BuildError, atomic_json, digest, open_table
from audit_hf_medications import classify, NAMES, PAIR_ARMS
from hf_joint_evidence import evidence

CORE = ('medication_orders', 'hospital_diagnoses', 'outpatient_diagnoses', 'echo_studies')
ARMS = dict(zip(PAIR_ARMS['COMET'], ('carvedilol_candidate', 'metoprolol_tartrate_candidate')))


@lru_cache(maxsize=20000)
def family_bucket(names):
    words = set(re.findall('[a-z]+', ' '.join(names).lower()))
    if not words & {'carvedilol','metoprolol','coreg','coregcr','lopressor','toprol'}:
        return None
    return classify(names) or 'unresolved_family'


def discover(root):
    matches = []
    for path in sorted(Path(root).glob('*/snapshot/manifest.json')):
        m = json.loads(path.read_text())
        if m.get('status') == 'complete' and set(CORE) <= m.get('stages', {}).keys():
            matches.append(path.parent)
    if len(matches) != 1:
        raise BuildError('require_exactly_one_complete_core_snapshot_or_explicit_snapshot')
    return matches[0]


def records(table, columns, patient_keys=None):
    if not set(columns) <= set(table.schema.names):
        raise BuildError('required_candidate_columns_absent')
    scanned = 0
    if patient_keys is None:
        batches=table.scanner(columns=columns, batch_size=16384, use_threads=False).to_batches()
    else:
        from candidate_event_cache import filtered_batches
        batches=filtered_batches(table,patient_keys,columns)
    for batch in batches:
        data = batch.to_pydict()
        for values in zip(*(data[c] for c in columns)):
            yield dict(zip(columns, values))
        scanned += batch.num_rows
        if scanned // 5000000 != (scanned-batch.num_rows) // 5000000:
            print('Scanned projected records: ' + str(scanned), flush=True)


def ef_state(value):
    if value is None: return 'missing'
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value): return 'invalid'
    if value <= 1 or value > 100: return 'scale_or_range_unresolved'
    if value < 35: return 'gt1_lt35'
    if value == 35: return 'eq35'
    return 'gt35_le100'


def run(snapshot, output):
    import pyarrow as pa
    import pyarrow.parquet as pq
    started = time.monotonic()
    snapshot, output = Path(snapshot), Path(output)
    if not snapshot.is_absolute() or not output.is_absolute() or output.is_symlink():
        raise BuildError('absolute_nonsymlink_paths_required')
    snapshot, output = snapshot.resolve(), output.resolve()
    if snapshot == output or snapshot in output.parents or output in snapshot.parents:
        raise BuildError('output_snapshot_overlap')
    manifest_hash = digest(snapshot/'manifest.json')
    tables = {name: open_table(snapshot, name) for name in CORE}
    part_stats = {p: (Path(p).stat().st_size, Path(p).stat().st_mtime_ns) for t in tables.values() for p in t.files}
    os.umask(0o077)
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    report = dict(version='comet_candidates_v1', status='building', counts_valid=False,
                  restricted_until_reviewed=True, clinically_eligible_patients=None,
                  interpretation='First lexical candidate across both arms; not validated drugs, HF phenotype, new use, dispensing or trial eligibility.',
                  clinical_index_frozen=False, prior_history_scope='Lexical carvedilol/metoprolol family only, not all beta-blockers; no washout exclusion.',
                  timing='Strict prior calendar days; source availability unverified. DX_DATE and CALC_DX_DATE are independent views.',
                  identity='Exact trimmed shared keys, not validated cross-source linkage.',
                  same_day_policy='Competing candidate arms retained as unresolved; no arbitrary assignment.',
                  source_snapshot=str(snapshot), core_manifest_sha256=manifest_hash,
                  implementation_sha256={name:digest(Path(__file__).with_name(name)) for name in
                      ('build_comet_candidates.py','build_shared_tables.py','audit_hf_medications.py','hf_joint_evidence.py')})
    atomic_json(output/'summary.json', report)
    db = sqlite3.connect(output/'restricted_candidates.sqlite')
    stage = 'medications'
    try:
        db.executescript('''PRAGMA temp_store=MEMORY;
        CREATE TABLE medication_evidence(patient TEXT, day TEXT, bucket TEXT, candidate_arm TEXT, source_row INTEGER);
        CREATE INDEX medication_patient_day ON medication_evidence(patient,day);
        ''')
        med_cols = ['__patient_key','__day_ORDER_INST','__source_row','ORDERING_MODE','ORDER_CLASS',*NAMES]
        anchors = {}; med_rows = 0
        for row in records(tables['medication_orders'], med_cols):
            med_rows += 1
            names = tuple(row[n] or '' for n in NAMES)
            if any(len(n)>4096 for n in names): raise BuildError('oversized_medication_name')
            # Broad family evidence is deliberately only a lexical history flag.
            bucket = family_bucket(names)
            if bucket is None: continue
            patient, day = row['__patient_key'], row['__day_ORDER_INST']
            if not patient: continue
            arm = ARMS.get(bucket) if (row['ORDERING_MODE'] or '').strip().lower() == 'outpatient' and (row['ORDER_CLASS'] or '').strip().lower() in ('normal','print') else None
            db.execute('INSERT INTO medication_evidence VALUES(?,?,?,?,?)',
                       (patient, day.isoformat() if day else None, bucket, arm, row['__source_row']))
            if arm and day:
                old = anchors.get(patient)
                if old is None or day < old['day']:
                    anchors[patient] = dict(day=day, arms={arm}, rows={row['__source_row']})
                elif day == old['day']:
                    old['arms'].add(arm); old['rows'].add(row['__source_row'])
                if len(anchors)>1000000: raise BuildError('candidate_memory_limit_exceeded')
        db.commit()
        if not anchors: raise BuildError('no_candidate_anchors')
        print('Candidate anchors prepared; scanning echo and diagnosis projections.', flush=True)
        stage = 'echo'
        echoes = {}; echo_unknown = set()
        for row in records(tables['echo_studies'], ['__patient_key','__day_EchoDate','EF','__source_row']):
            patient = row['__patient_key']
            if patient not in anchors: continue
            day = row['__day_EchoDate']
            if day is None: echo_unknown.add(patient); continue
            if day >= anchors[patient]['day']: continue
            state = ef_state(row['EF']); old = echoes.get(patient)
            if old is None or day > old['day']:
                echoes[patient] = dict(day=day, states={state}, values={repr(row['EF'])}, rows={row['__source_row']})
            elif day == old['day']:
                old['states'].add(state); old['values'].add(repr(row['EF'])); old['rows'].add(row['__source_row'])
        dx_flags = {patient: set() for patient in anchors}
        for name in CORE[1:3]:
            stage = name
            for row in records(tables[name], ['__patient_key','__day_DX_DATE','__day_CALC_DX_DATE','CURRENT_ICD10_LIST']):
                patient = row['__patient_key']
                if patient not in anchors: continue
                hf, systolic = evidence(row['CURRENT_ICD10_LIST'] or '')
                if not hf: continue
                for view in ('DX_DATE','CALC_DX_DATE'):
                    day = row['__day_'+view]
                    relation = 'undated' if day is None else 'before' if day < anchors[patient]['day'] else 'same_day' if day == anchors[patient]['day'] else 'after'
                    dx_flags[patient].add(view+'_hf_'+relation)
                    if systolic: dx_flags[patient].add(view+'_systolic_'+relation)
        stage = 'candidate_output'
        summaries = Counter(); arm_counts = Counter(); history_counts = Counter(); result = []
        for patient, anchor in sorted(anchors.items()):
            day = anchor['day']; arm = next(iter(anchor['arms'])) if len(anchor['arms'])==1 else 'competing_arms_same_day'
            arm_counts[arm] += 1
            prior, undated = db.execute('''SELECT
                COALESCE(SUM(day>=? AND day<?),0),COALESCE(SUM(day IS NULL),0)
                FROM medication_evidence WHERE patient=?''',
                ((day-timedelta(days=365)).isoformat(),day.isoformat(),patient)).fetchone()
            if prior: history_counts[(arm,'prior_365d_family_order_found')] += 1
            if undated: history_counts[(arm,'undated_family_order_found')] += 1
            echo = echoes.get(patient)
            lag = (day-echo['day']).days if echo else None
            state = ('no_prior_echo' if echo is None else 'stale_over365' if lag>365 else
                     'latest_day_disagreement' if len(echo['values'])>1 else next(iter(echo['states'])))
            record = dict(patient_key=patient, candidate_arm=arm, candidate_order_day=day,
                candidate_order_source_rows=sorted(anchor['rows']), prior_365d_family_order_records=prior,
                undated_family_order_records=undated, latest_prior_echo_day=echo['day'] if echo else None,
                latest_prior_echo_lag_days=lag, latest_prior_echo_state=state,
                latest_prior_echo_source_rows=sorted(echo['rows']) if echo else [],
                undated_echo_present=patient in echo_unknown)
            for view in ('DX_DATE','CALC_DX_DATE'):
                flags = dx_flags[patient]
                hf = view+'_hf_before' in flags; systolic = view+'_systolic_before' in flags
                record[view+'_prior_hf_evidence'] = hf; record[view+'_prior_systolic_evidence'] = systolic
                record[view+'_hf_timing_flags'] = sorted(f.removeprefix(view+'_') for f in flags if f.startswith(view+'_'))
                group = ('systolic_code' if systolic else 'other_hf_code' if hf else 'no_prior_hf_code_found')
                summaries[(arm,view,group,state)] += 1
            result.append(record)
        # Explicit schema prevents all-null dates/lists acquiring incompatible types.
        schema = pa.schema([
            ('patient_key',pa.string()),('candidate_arm',pa.string()),('candidate_order_day',pa.date32()),
            ('candidate_order_source_rows',pa.list_(pa.int64())),('prior_365d_family_order_records',pa.int64()),
            ('undated_family_order_records',pa.int64()),('latest_prior_echo_day',pa.date32()),
            ('latest_prior_echo_lag_days',pa.int64()),('latest_prior_echo_state',pa.string()),
            ('latest_prior_echo_source_rows',pa.list_(pa.int64())),('undated_echo_present',pa.bool_()),
            *[(view+suffix,typ) for view in ('DX_DATE','CALC_DX_DATE') for suffix,typ in
              [('_prior_hf_evidence',pa.bool_()),('_prior_systolic_evidence',pa.bool_()),('_hf_timing_flags',pa.list_(pa.string()))]]
        ])
        pending = output/'restricted_candidates.partial.parquet'
        pq.write_table(pa.Table.from_pylist(result,schema=schema),pending,compression='zstd')
        if digest(snapshot/'manifest.json')!=manifest_hash or any((Path(p).stat().st_size,Path(p).stat().st_mtime_ns)!=s for p,s in part_stats.items()):
            raise BuildError('core_snapshot_changed')
        with pq.ParquetFile(pending) as check:
            if check.metadata.num_rows!=len(anchors): raise BuildError('candidate_output_count_mismatch')
        pending.rename(output/'restricted_candidates.parquet')
        db.commit()
        atomic_json(output/'restricted_manifest.json',dict(version='comet_candidates_v1', core_snapshot=str(snapshot),
            core_manifest_sha256=manifest_hash, candidate_sha256=digest(output/'restricted_candidates.parquet'),
            mapping='hf_name_screen_v1_and_provisional_I50_only', rows=len(anchors),
            lineage='Medication/echo ordinals reference named core tables; diagnosis flags are provisional aggregates, no phenotype qualification.',
            settings=dict(echo_window_days=365,history_days=365,prior_history_exclusion=False,cohort_eligibility_applied=False)))
        report.update(status='complete_provisional_candidates',counts_valid=True,medication_records_scanned=med_rows,
            candidate_patient_keys=len(anchors),by_arm=dict(arm_counts),
            history_flags=[dict(arm=a,flag=f,patient_keys=n) for (a,f),n in sorted(history_counts.items())],
            evidence_groups=[dict(arm=a,date_view=v,hf_evidence=h,echo_state=e,patient_keys=n) for (a,v,h,e),n in sorted(summaries.items())])
    except Exception as exc:
        report.update(status='failed_candidates_invalid',counts_valid=False,failure_stage=stage,
                      reason=str(exc) if isinstance(exc,BuildError) else 'candidate_build_failed_no_raw_error_export')
        raise
    finally:
        db.close(); classify.cache_clear(); family_bucket.cache_clear()
        report['elapsed_seconds'] = round(time.monotonic()-started,3)
        atomic_json(output/'summary.json',report)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    choice=p.add_mutually_exclusive_group(required=True)
    choice.add_argument('--snapshot',type=Path)
    choice.add_argument('--shared-root',type=Path)
    p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args()
    try:
        snapshot=a.snapshot if a.snapshot else discover(a.shared_root)
        print('Using completed core snapshot: '+str(snapshot),flush=True)
        r=run(snapshot,a.output_dir)
    except Exception as exc:
        print('Stopped: '+(str(exc) if isinstance(exc,BuildError) else type(exc).__name__),flush=True)
        return 1
    print('Finished: '+r['status']+'. Review summary.json; patient tables stay on H100.',flush=True)
    return 0

if __name__=='__main__': raise SystemExit(main())
