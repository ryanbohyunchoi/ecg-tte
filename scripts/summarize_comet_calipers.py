#!/usr/bin/env python3
"""Summarize all three requested exploratory cutoffs, including failed runs."""
import json
from pathlib import Path
import sys
from build_shared_tables import atomic_json, digest

CUTOFFS=('0.20','0.30','0.40')

def summarize(root):
    result=dict(version='comet_caliper_grid_v1',restricted_until_reviewed=True,
        ready_for_effects=False,interpretation='Exploratory sensitivity after no-caliper review. Report all cutoffs; no best-threshold selection.',runs=[])
    signatures=[]
    for cutoff in CUTOFFS:
        p=root/('caliper-'+cutoff)/'report'/'summary.json'
        entry=dict(caliper=float(cutoff),report=str(p.parent))
        if not p.is_file():entry.update(status='missing_summary',counts_valid=False)
        else:
            s=json.loads(p.read_text());entry.update(status=s['status'],counts_valid=s.get('counts_valid',False),source_summary_sha256=digest(p))
            entry['assignment_objective']=s.get('assignment_objective')
            if s.get('counts_valid') and s.get('status')=='complete_exploratory_comparison':
                if s.get('version')!='comet_cosine_comparison_v4_caliper' or s['contract']['cosine_caliper']!=float(cutoff):
                    raise ValueError('caliper_contract_mismatch')
                signatures.append((s['common_rows'],s['denominators'],s['contract']['checkpoint_weights_sha256']))
                entry['common_rows']=s['common_rows'];entry['denominators']=s['denominators']
                entry['methods']={}
                for method,rows in s['methods'].items():
                    entry['methods'][method]={field:dict(min=min(r[field] for r in rows),max=max(r[field] for r in rows)) for field in (
                        'pairs','carvedilol_retention','metoprolol_retention','mean_abs_smd','max_abs_smd','features_ge_0_1','undefined_smd')}
            else:entry['reason']=s.get('reason','not_complete')
        result['runs'].append(entry)
    if signatures and any(x!=signatures[0] for x in signatures):raise ValueError('grid_population_or_checkpoint_mismatch')
    result['status']='complete_grid' if all(r['counts_valid'] and r['status']=='complete_exploratory_comparison' for r in result['runs']) else 'grid_contains_incomplete_runs'
    atomic_json(root/'grid_summary.json',result)
    return result

if __name__=='__main__':
    print(json.dumps(summarize(Path(sys.argv[1])),indent=2))
