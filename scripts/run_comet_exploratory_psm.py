#!/usr/bin/env python3
"""Exploratory design diagnostics only; pending trace review is never auto-approved."""
import argparse
import csv
import json
import math
import os
from pathlib import Path
import subprocess
import time
from build_shared_tables import BuildError, atomic_json, digest
from review_comet_mice_pilot import run as review


def check_pairs(pairs,scores,caliper):
    lookup={r['patient_key']:float(r['logit']) for r in scores}
    if len(lookup)!=len(scores) or any(not math.isfinite(v) for v in lookup.values()):raise BuildError('invalid_scores')
    treated=[r['carvedilol_key'] for r in pairs];control=[r['metoprolol_key'] for r in pairs]
    if len(set(treated))!=len(treated) or len(set(control))!=len(control) or set(treated)&set(control):raise BuildError('matching_reused_patient')
    for a,b in zip(treated,control):
        if a not in lookup or b not in lookup or abs(lookup[a]-lookup[b])>caliper+1e-12:raise BuildError('caliper_violation')


def run(report,output,rscript,refined=False):
    report,output=Path(report),Path(output)
    if any(not p.is_absolute() or p.is_symlink() for p in (report,output)):raise BuildError('absolute_nonsymlink_paths_required')
    if report.resolve()==output.resolve() or report.resolve() in output.resolve().parents or output.resolve() in report.resolve().parents:raise BuildError('output_overlap')
    source=json.loads((report/'summary.json').read_text())
    if source.get('version')!='comet_mice_pilot_v2_ordered_bp':raise BuildError('ordered_bp_pilot_required')
    os.umask(0o077);output.mkdir(parents=True,exist_ok=False,mode=0o700)
    summary=dict(version='comet_exploratory_psm_v2_refined' if refined else 'comet_exploratory_psm_v1',status='running',counts_valid=False,ready_for_effects=False,restricted_until_reviewed=True)
    atomic_json(output/'summary.json',summary);start=time.monotonic()
    try:
        checked=review(report,output/'input_review')
        if checked['startup_abi_warning_detected'] or checked['bp_inconsistent_patient_imputation_rows']:raise BuildError('unresolved_input_warning_or_bp')
        needed={'restricted_missingness_mask.json','chain_traces.rds'}|{f'restricted_completed_{i:02d}.csv' for i in range(1,source['imputations']+1)}
        manifest=json.loads((report/'manifest.json').read_text())
        if not needed<=set(manifest['outputs']):raise BuildError('unmanifested_psm_inputs')
        env=dict(os.environ);(output/'tmp').mkdir();env['TMPDIR']=str(output/'tmp')
        with (output/'restricted_psm_engine.log').open('w') as log:
            proc=subprocess.run([rscript,'--vanilla',str(Path(__file__).with_name('comet_exploratory_psm.R')),str(report),str(output),'refined' if refined else 'original'],env=env,stdout=log,stderr=log)
        if proc.returncode:raise BuildError('psm_engine_failed_review_private_log')
        result=json.loads((output/'psm_summary.json').read_text())
        keys=json.loads((report/'restricted_row_keys.json').read_text())
        import pyarrow.parquet as pq
        original=pq.read_table(Path(source['source_report'])/'restricted_cleaned_baseline.parquet').to_pylist()
        arm={r['patient_key']:r['treatment_arm'] for r in original}
        for info in result['imputations']:
            i=info['imputation']
            with (output/f'restricted_pairs_{i:02d}.csv').open() as f:pairs=list(csv.DictReader(f))
            with (output/f'restricted_scores_{i:02d}.csv').open() as f:scores=list(csv.DictReader(f))
            if [r['patient_key'] for r in scores]!=keys or len(pairs)!=info['pairs']:raise BuildError('matching_roster_mismatch')
            check_pairs(pairs,scores,info['caliper'])
            if any(arm.get(r['carvedilol_key'])!='carvedilol_candidate' or arm.get(r['metoprolol_key'])!='metoprolol_tartrate_candidate' for r in pairs):raise BuildError('matching_arm_mismatch')
        for name,h in manifest['outputs'].items():
            if digest(report/name)!=h:raise BuildError('pilot_changed_during_matching')
        summary.update(status='complete_exploratory_design_requires_review',counts_valid=True,rows=source['rows'],denominators=source['denominators'],source_report=str(report),
                       trace_review='pending_not_auto_approved',**result,
                       specification=('REFINED: EF replaced with natural spline knots30,50 boundaries1,100; nonconstant original missingness flags fitted; exact linear dependencies removed by declared QR rule and reported. Common clinical evaluation set unchanged. ' if refined else '')+'32 clinical covariates, main-effects unpenalized logistic PS; sex dummy coded. Original missingness evaluated; fitting governed by declared version. Carvedilol treated; 1:1 greedy descending treated logit, no replacement, caliper0.2 pooled within-arm pre-match SD(logit). SMD denominator fixed pre-match within each imputation. No effect estimation.')
        atomic_json(output/'manifest.json',dict(version=summary['version'],input_manifest_sha256=digest(report/'manifest.json'),input_summary_sha256=digest(report/'summary.json'),
            code_checksums={p.name:digest(p) for p in (Path(__file__),Path(__file__).with_name('comet_exploratory_psm.R'))},outputs={p.name:digest(p) for p in output.iterdir() if p.is_file() and p.name!='summary.json'}))
    except Exception as e:
        summary.update(status='failed_exploratory_psm',counts_valid=False,reason=str(e) if isinstance(e,BuildError) else type(e).__name__);raise
    finally:
        summary['elapsed_seconds']=round(time.monotonic()-start,3);atomic_json(output/'summary.json',summary)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',required=True,type=Path);p.add_argument('--output-dir',required=True,type=Path);p.add_argument('--rscript',default='Rscript');p.add_argument('--refined',action='store_true');a=p.parse_args()
    try:run(a.report,a.output_dir,a.rscript,a.refined)
    except Exception as e:print('Stopped: '+(str(e) if isinstance(e,BuildError) else type(e).__name__));return 1
    print('Exploratory matching complete; trace and balance review required. No effects estimated.');return 0
if __name__=='__main__':raise SystemExit(main())
