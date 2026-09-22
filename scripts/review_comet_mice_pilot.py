#!/usr/bin/env python3
"""Read-only saved MICE diagnostic review; no automatic convergence approval."""
import argparse
from collections import Counter, defaultdict
import csv
import json
import math
import os
from pathlib import Path
import statistics
import pyarrow.parquet as pq
from build_shared_tables import BuildError, atomic_json, digest
from audit_comet_numeric_candidates import FIELDS, profile
from run_comet_mice_pilot import validate_completed

VERSION = 'comet_mice_review_v1'


def summarize_ac(records, targets):
    groups = defaultdict(list)
    for row in records:
        if row['vrb'] not in targets: continue
        try: value = float(row['ac'])
        except (TypeError, ValueError): continue
        if math.isfinite(value): groups[row['vrb']].append((int(row['.it']), value))
    result = []
    for feature in sorted(targets):
        values = sorted(groups[feature])
        last = [v for _, v in values[-5:]]
        result.append(dict(feature=feature, finite_iterations=len(values),
                           final_ac=values[-1][1] if values else None,
                           last5_mean_abs_ac=statistics.mean(map(abs,last)) if last else None,
                           interpretation='Descriptive lag-1 autocorrelation; no convergence threshold or pass.'))
    return result


def bp_review(original, completed, imputation):
    counts = Counter(); keys = set()
    for source, row in zip(original, completed):
        if row['sbp'] >= row['dbp']: continue
        keys.add(source['patient_key'])
        basis = ('both_imputed' if source['sbp'] is None and source['dbp'] is None else
                 'sbp_imputed' if source['sbp'] is None else
                 'dbp_imputed' if source['dbp'] is None else 'both_observed')
        counts[row['treatment_arm'],basis] += 1
    return [dict(imputation=imputation,arm=a,basis=b,rows=n) for (a,b),n in sorted(counts.items())], keys


def run(report, output):
    report, output = Path(report), Path(output)
    if any(not p.is_absolute() or p.is_symlink() for p in (report,output)):
        raise BuildError('absolute_nonsymlink_paths_required')
    if report.resolve()==output.resolve() or report.resolve() in output.resolve().parents or output.resolve() in report.resolve().parents:
        raise BuildError('source_output_overlap')
    s=json.loads((report/'summary.json').read_text());m=json.loads((report/'manifest.json').read_text())
    if s.get('version')!='comet_mice_pilot_v1' or m.get('version')!=s['version'] or s.get('status')!='complete_pilot_requires_review' or s.get('counts_valid') is not True:
        raise BuildError('complete_pilot_required')
    checks={report/n:digest(report/n) for n in ('summary.json','manifest.json')}
    for name,h in m['outputs'].items():
        p=report/name
        if p.is_symlink() or report.resolve() not in p.resolve().parents or digest(p)!=h:raise BuildError('pilot_artifact_changed')
        checks[p]=h
    source=Path(s['source_report'])/'restricted_cleaned_baseline.parquet'
    if not source.is_absolute() or source.is_symlink() or m['input_checksums'].get(str(source))!=digest(source):raise BuildError('original_baseline_changed')
    if output.resolve()==source.parent.resolve() or source.parent.resolve() in output.resolve().parents or output.resolve() in source.parent.resolve().parents:raise BuildError('output_parent_overlap')
    checks[source]=digest(source)
    needed={'model_spec.json','restricted_row_keys.json','restricted_engine.log'}|{f'restricted_completed_{i:02d}.parquet' for i in range(1,s['imputations']+1)}
    if not needed<=set(m['outputs']):raise BuildError('required_artifacts_unmanifested')
    spec=json.loads((report/'model_spec.json').read_text()); original=pq.read_table(source).to_pylist()
    if len(original)!=s['rows'] or dict(Counter(r['treatment_arm'] for r in original))!=s['denominators']:raise BuildError('roster_mismatch')
    keys=[r['patient_key'] for r in original]
    if len(set(keys))!=len(keys) or json.loads((report/'restricted_row_keys.json').read_text())!=keys:raise BuildError('row_key_mismatch')
    os.umask(0o077);output.mkdir(parents=True,exist_ok=False,mode=0o700)
    result=dict(version=VERSION,status='running',counts_valid=False,ready_for_psm=False,restricted_until_reviewed=True)
    atomic_json(output/'summary.json',result)
    try:
        comparisons=defaultdict(list); bp=[]; affected=set()
        for i in range(1,s['imputations']+1):
            saved=pq.read_table(report/f'restricted_completed_{i:02d}.parquet').to_pylist()
            if [r['patient_key'] for r in saved]!=keys or any(r['index_date']!=o['index_date'] for o,r in zip(original,saved)):raise BuildError('completed_identity_changed')
            completed=validate_completed(original,[{f:r[f] for f in spec['columns']} for r in saved],spec)
            records,patients=bp_review(original,completed,i);bp.extend(records);affected.update(patients)
            for arm in sorted(s['denominators']):
                for feature in FIELDS[1:]:
                    observed=[r[feature] for r in original if r['treatment_arm']==arm and r[feature] is not None]
                    imputed=[r[feature] for o,r in zip(original,completed) if r['treatment_arm']==arm and o[feature] is None]
                    po,pi=profile(observed),profile(imputed)
                    if po['quantiles'] and pi['quantiles']:
                        comparisons[arm,feature].append((statistics.median(imputed)-statistics.median(observed),pi['quantiles']['0.01'],pi['quantiles']['0.99']))
        targets={f for f in spec['columns'] if any(r[f] is None for r in original)}
        ac=[]
        if 'convergence.csv' in m['outputs']:
            with (report/'convergence.csv').open() as stream: ac=summarize_ac(list(csv.DictReader(stream)),targets)
        with (report/'restricted_engine.log').open('rb') as stream: log=stream.read(1048576).lower()
        distribution=[]
        for (arm,feature),values in sorted(comparisons.items()):
            obs=profile([r[feature] for r in original if r['treatment_arm']==arm and r[feature] is not None])
            distribution.append(dict(arm=arm,feature=feature,observed_median=obs['quantiles']['0.5'],
                imputed_minus_observed_median_range=[min(v[0] for v in values),max(v[0] for v in values)],
                imputed_p01_min=min(v[1] for v in values),imputed_p99_max=max(v[2] for v in values)))
        if any(digest(p)!=h for p,h in checks.items()):raise BuildError('inputs_changed')
        result.update(status='complete_diagnostic_review',counts_valid=True,source_report=str(report),rows=s['rows'],
            imputations=s['imputations'],engine=s['engine'],startup_abi_warning_detected=b'abi version mismatch' in log,
            bp_inconsistent_patient_imputation_rows=sum(r['rows'] for r in bp),bp_unique_patients=len(affected),bp_provenance=bp,
            autocorrelation=ac,distribution_comparisons=distribution,
            interpretation='Diagnostics only. Distribution differences are not covariate balance tests and are not required to be zero. Autocorrelation is not proof of convergence or MAR. No values changed, no matching or effects.',
            remaining_review=['Inspect existing chain_traces.pdf for drift/mixing','Review distribution differences with missingness mechanisms','Resolve dependency ABI warning before final environment freeze','Review BP provenance before specifying any constraint'])
        atomic_json(output/'manifest.json',dict(version=VERSION,input_checksums={str(p):h for p,h in checks.items()},script_sha256=digest(Path(__file__))))
    except Exception as e:
        result.update(status='failed_review',counts_valid=False,reason=str(e) if isinstance(e,BuildError) else type(e).__name__);raise
    finally:atomic_json(output/'summary.json',result)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    try:run(a.report,a.output_dir)
    except Exception as e:print('Stopped: '+(str(e) if isinstance(e,BuildError) else type(e).__name__));return 1
    print('Saved pilot review complete; review summary.json locally. No MICE rerun.');return 0
if __name__=='__main__':raise SystemExit(main())
