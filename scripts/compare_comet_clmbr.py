#!/usr/bin/env python3
"""Outcome-blind common-population cosine versus unchanged PSM comparison."""
import argparse
from collections import Counter
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import numpy as np
import pyarrow.parquet as pq
from build_shared_tables import BuildError, atomic_json, digest
from review_comet_mice_pilot import run as review
from run_comet_exploratory_psm import check_pairs

VERSION = 'comet_cosine_comparison_v1'
CONTRACT = dict(version=VERSION, primary_comparator='original_psm',
    secondary_comparator='previously_refined_psm_disclosed_post_diagnostic_refinement',
    cosine='L2 normalization; 1-dot; greedy carvedilol order SHA256(comet_cosine_v1|patient_key), lexical key ties; control lexical key ties',
    checkpoint_weights_sha256='f56e2ece082b9daf87767c7de93419db1b6c0eaf21311e06c8f329b7ab4b81a2',
    ratio='1:1', replacement=False, cosine_caliper=None,
    psm='Unchanged original/refined formulas, descending treated logit, 0.2 pooled within-arm logit SD caliper',
    interpretation='Method-bundle comparison: assignment order and support rules differ. Retention differs; no isolated metric superiority claim.',
    evaluation='Same common population and original missingness; fixed pre-match SMD denominator per saved imputation; no outcome use or MICE refitting')


def cosine_pairs(keys, arms, vectors):
    x = np.asarray(vectors, dtype=np.float64)
    if x.ndim != 2 or len(x) != len(keys) or len(arms) != len(keys) or len(set(keys)) != len(keys):
        raise BuildError('invalid_embedding_roster')
    norms = np.linalg.norm(x, axis=1)
    if not np.isfinite(x).all() or not np.isfinite(norms).all() or np.any(norms <= 0):
        raise BuildError('invalid_embedding_values')
    if set(arms) != {'carvedilol_candidate', 'metoprolol_tartrate_candidate'}:
        raise BuildError('invalid_embedding_arms')
    x = x / norms[:, None]
    treated = sorted((i for i,a in enumerate(arms) if a=='carvedilol_candidate'),
        key=lambda i:(hashlib.sha256(('comet_cosine_v1|'+keys[i]).encode()).digest(),keys[i]))
    controls = sorted((i for i,a in enumerate(arms) if a=='metoprolol_tartrate_candidate'),key=lambda i:keys[i])
    result=[]
    for t in treated:
        if not controls: break
        distances=1-np.clip(x[controls]@x[t],-1,1)
        k=int(np.argmin(distances)); c=controls.pop(k)
        result.append(dict(carvedilol_key=keys[t],metoprolol_key=keys[c],cosine_distance=float(distances[k])))
    if len(result)<2: raise BuildError('insufficient_matches')
    return result


def read_json(p): return json.loads(p.read_text())
def read_csv(p):
    with p.open() as f: return list(csv.DictReader(f))
def write_csv(p,rows):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def verified(root):
    m=read_json(root/'manifest.json'); checks={root/n:digest(root/n) for n in ('summary.json','manifest.json')}
    for name,h in m['outputs'].items():
        p=root/name
        if p.is_symlink() or root.resolve() not in p.resolve().parents or digest(p)!=h: raise BuildError('input_manifest_mismatch')
        checks[p]=h
    return m,checks


def run(embeddings,mice,output,rscript):
    if any(not p.is_absolute() or p.is_symlink() for p in (embeddings,mice,output)): raise BuildError('absolute_nonsymlink_paths_required')
    for root in (embeddings,mice):
        if root.resolve()==output.resolve() or root.resolve() in output.resolve().parents or output.resolve() in root.resolve().parents: raise BuildError('output_overlap')
    os.umask(0o077);output.mkdir(parents=True,exist_ok=False)
    summary=dict(version=VERSION,status='running',counts_valid=False,ready_for_effects=False,restricted_until_reviewed=True)
    atomic_json(output/'summary.json',summary);atomic_json(output/'contract.json',CONTRACT);start=time.monotonic()
    try:
        em,checks=verified(embeddings); mm,mc=verified(mice);checks.update(mc)
        es=read_json(embeddings/'summary.json');ms=read_json(mice/'summary.json')
        if es.get('status')!='complete_embeddings_requires_review' or es.get('counts_valid') is not True or es.get('limit')!=0 or es.get('numeric_mode')!='code-only' or es.get('max_tokens')!=4096: raise BuildError('full_codes_only_embeddings_required')
        if em.get('model_sha256',{}).get('model.safetensors')!=CONTRACT['checkpoint_weights_sha256']: raise BuildError('checkpoint_changed')
        if ms.get('version')!='comet_mice_pilot_v2_ordered_bp': raise BuildError('ordered_bp_required')
        checked=review(mice,output/'input_review')
        if checked['startup_abi_warning_detected'] or checked['bp_inconsistent_patient_imputation_rows']: raise BuildError('unresolved_input_warning_or_bp')
        spec=read_json(mice/'model_spec.json'); keys=read_json(mice/'restricted_row_keys.json');mask=read_json(mice/'restricted_missingness_mask.json')
        required={'model_spec.json','restricted_row_keys.json','restricted_missingness_mask.json','chain_traces.rds'}|{f'restricted_completed_{i:02d}.parquet' for i in range(1,spec['m']+1)}
        if not required<=set(mm['outputs']): raise BuildError('unmanifested_mice_inputs')
        baseline=Path(ms['source_report'])/'restricted_cleaned_baseline.parquet'
        original=pq.read_table(baseline).to_pylist(); checks[baseline]=digest(baseline)
        lookup={r['patient_key']:r for r in original}
        files=sorted(embeddings.glob('restricted_embeddings_part-*.parquet'))
        if not files or any(p.name not in em['outputs'] for p in files): raise BuildError('unmanifested_embeddings')
        if {p.name for p in files}!={n for n in em['outputs'] if n.startswith('restricted_embeddings_part-')}: raise BuildError('embedding_partition_mismatch')
        rows=[r for p in files for r in pq.read_table(p).to_pylist()]
        bykey={r['patient_key']:r for r in rows}
        if len(bykey)!=len(rows) or len(rows)!=es.get('totals',{}).get('encoded'): raise BuildError('embedding_count_mismatch')
        for k,r in bykey.items():
            if k not in lookup or any(r[f]!=lookup[k][f] for f in ('treatment_arm','index_date')) or len(r['embedding'])!=768: raise BuildError('embedding_identity_mismatch')
        if 'restricted_patient_status.parquet' not in em['outputs']: raise BuildError('unmanifested_embedding_status')
        status=pq.read_table(embeddings/'restricted_patient_status.parquet').to_pylist()
        if len(status)!=len(keys) or {r['patient_key'] for r in status}!=set(keys): raise BuildError('embedding_status_roster_mismatch')
        if {r['patient_key'] for r in status if r['status']=='encoded'}!=set(bykey): raise BuildError('embedding_status_mismatch')
        for f in set(spec['columns'])-{'treatment_arm'}:
            if mask.get(f)!=[r[f] is None for r in original]: raise BuildError('missingness_mask_mismatch')
        selected=[j for j,k in enumerate(keys) if k in bykey]; common=[keys[j] for j in selected]
        arms=[lookup[k]['treatment_arm'] for k in common]
        pairs=cosine_pairs(common,arms,[bykey[k]['embedding'] for k in common])
        pair_path=output/'restricted_cosine_pairs.csv';write_csv(pair_path,pairs)
        subset=output/'restricted_common_inputs';subset.mkdir()
        atomic_json(subset/'model_spec.json',spec);atomic_json(subset/'restricted_row_keys.json',common)
        atomic_json(subset/'restricted_missingness_mask.json',{f:[v[j] for j in selected] for f,v in mask.items()})
        shutil.copyfile(mice/'chain_traces.rds',subset/'chain_traces.rds')
        for i in range(1,spec['m']+1):
            completed=pq.read_table(mice/f'restricted_completed_{i:02d}.parquet').to_pylist()
            write_csv(subset/f'restricted_completed_{i:02d}.csv',[{f:completed[j][f] for f in spec['columns']} for j in selected])
        engine=Path(__file__).with_name('comet_exploratory_psm.R').resolve()
        runner=output/'run_comparison.R'
        runner.write_text('a<-commandArgs(trailingOnly=TRUE)\nsource(a[1])\nmain(a[2],a[3],a[4]=="refined",if(a[4]=="cosine") a[5] else NULL)\n')
        all_balance=[];all_observed=[];method_summaries={}
        for method in ('original','refined','cosine'):
            dest=output/method;dest.mkdir()
            with (dest/'restricted_engine.log').open('w') as log:
                proc=subprocess.run([rscript,'--vanilla',str(runner),str(engine),str(subset),str(dest),method,str(pair_path)],stdout=log,stderr=log)
            if proc.returncode: raise BuildError('comparison_engine_failed_review_private_log')
            result=read_json(dest/'psm_summary.json')
            for info in result['imputations']:
                i=info['imputation'];saved=read_csv(dest/f'restricted_pairs_{i:02d}.csv');scores=read_csv(dest/f'restricted_scores_{i:02d}.csv')
                if [r['patient_key'] for r in scores]!=common or len(saved)!=info['pairs']: raise BuildError('matching_roster_mismatch')
                if method!='cosine': check_pairs(saved,scores,info['caliper'])
                elif saved!=[{f:r[f] for f in ('carvedilol_key','metoprolol_key')} for r in pairs]: raise BuildError('cosine_pairs_changed')
                if method=='cosine': info.pop('caliper',None)
            method_summaries[method]=result['imputations']
            all_observed.extend(dict(method=method,**r) for r in read_csv(dest/'observed_balance_by_imputation.csv'))
            all_balance.extend(dict(method=method,**r) for r in read_csv(dest/'balance_by_imputation.csv'))
        write_csv(output/'comparison_balance.csv',all_balance)
        write_csv(output/'comparison_observed_balance.csv',all_observed)
        plot_script=Path(__file__).with_name('plot_comet_method_comparison.R').resolve()
        with (output/'restricted_plot.log').open('w') as log:
            plotted=subprocess.run([rscript,'--vanilla',str(plot_script),str(output)],stdout=log,stderr=log)
        if plotted.returncode: raise BuildError('comparison_plot_failed')
        for p,h in checks.items():
            if digest(p)!=h: raise BuildError('input_changed_during_comparison')
        summary.update(status='complete_exploratory_comparison',counts_valid=True,common_rows=len(common),denominators=dict(Counter(arms)),excluded_without_embedding=len(keys)-len(common),excluded_by_arm=dict(Counter(lookup[k]['treatment_arm'] for k in keys if k not in bykey)),cosine_distance_quantiles={str(q):float(np.quantile([r['cosine_distance'] for r in pairs],q)) for q in (0,.25,.5,.75,.95,1)},methods=method_summaries,contract=CONTRACT,trace_review='pending_not_auto_approved')
        atomic_json(output/'manifest.json',dict(version=VERSION,input_checksums={str(p):h for p,h in checks.items()},code_checksums={str(p):digest(p) for p in (Path(__file__).resolve(),engine,plot_script)},outputs={str(p.relative_to(output)):digest(p) for p in output.rglob('*') if p.is_file() and p.name!='summary.json'}))
    except Exception as e:
        summary.update(status='failed_comparison',reason=str(e) if isinstance(e,BuildError) else type(e).__name__);raise
    finally:
        summary['elapsed_seconds']=round(time.monotonic()-start,3);atomic_json(output/'summary.json',summary)
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('embeddings','mice','output-dir'): p.add_argument('--'+n,required=True,type=Path)
    p.add_argument('--rscript',required=True);a=p.parse_args()
    try: run(a.embeddings,a.mice,a.output_dir,a.rscript)
    except Exception as e: print('Stopped:',str(e) if isinstance(e,BuildError) else type(e).__name__);raise SystemExit(1)
    print('Comparison complete; review balance and retention. No effects estimated.')
