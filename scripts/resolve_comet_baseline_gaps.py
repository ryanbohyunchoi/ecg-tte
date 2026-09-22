#!/usr/bin/env python3
"""Version adult-range cohort and dated-record diagnosis candidates; draft lab identities."""
import argparse
from collections import Counter, defaultdict
import json
import os
from pathlib import Path
import re
import time
import pyarrow as pa
import pyarrow.parquet as pq
from build_shared_tables import BuildError, digest, atomic_json
from build_comet_cached_baseline import discover
from audit_comet_mapping_gaps import verify_parent, checked_records
from comet_cached_context import CachedContext
from build_comet_baseline_staging import DX, tokens, recorded_binary
from medication_quality import missing_kind

VERSION='comet_baseline_resolution_v1'
POLICY='Diagnosis features are recorded evidence on DX_DATE calendar days1-365 before unchanged index. Undated diagnoses are separate auxiliaries, not positives or blockers. Dated unresolved ICD10 cells block otherwise-negative features; positive evidence wins. Zero means no qualifying dated record, not disease absence. No ICD9 translation or date fallback.'
CODE=r'[A-Z][0-9][A-Z0-9](?:\.?[A-Z0-9]{1,4})?'


def strict_list(raw):
    """Accept complete code tokens with explicit delimiters/whitespace; never extract substrings."""
    if len(raw)>4096:raise BuildError('oversized_code_cell')
    if missing_kind(raw):return None
    raw=raw.strip().upper()
    if not re.fullmatch(CODE+r'(?:(?:\s*[,;|]\s*|\s+)'+CODE+r')*',raw):return None
    return {c.replace('.','') for c in re.split(r'[,;|\s]+',raw)}


def lab_draft(group):
    """Label-based draft only, never an approved analyte/unit mapping."""
    name=' '.join((group.get('component_name') or '').upper().split())
    target={'CREATININE':'creatinine','POTASSIUM':'potassium','SODIUM':'sodium','HEMOGLOBIN':'hemoglobin'}.get(name)
    specimen=' '.join((group.get(k) or '') for k in ('specimen_type','specimen_source')).upper()
    if any(w in specimen for w in ('URINE','FLUID','CSF')):return target,'non_target_specimen_review'
    if target is None:return None,'name_requires_review'
    return target,'exact_name_candidate_requires_specimen_and_unit_review'


def adult_rows(rows):
    kept=[];excluded=[]
    for r in rows:
        a=r['age_at_index']
        if a is None or not isinstance(a,(int,float)) or not 0<=a<=120:reason='age_unresolved_quarantine'
        elif a<18:reason='under18_excluded'
        else:kept.append(r);continue
        excluded.append(dict(patient_key=r['patient_key'],arm=r['treatment_arm'],reason=reason))
    return kept,excluded


def diagnosis_values(context,keys):
    positives=defaultdict(set);blocked=defaultdict(set);undated=defaultdict(set);qc=Counter();stamps={}
    for source in (context.core,context.dx):
        for name in ('hospital_diagnoses','outpatient_diagnoses'):
            print('Resolving dated diagnosis evidence: '+source.parent.name+'/'+name,flush=True)
            table=context.open(source,name)
            for r in checked_records(table,['__patient_key','__day_DX_DATE','CURRENT_ICD10_LIST'],patient_keys=keys):
                k=r['__patient_key'];day=r['__day_DX_DATE'];index=context.anchors[k]['candidate_order_day']
                if day is not None and not 1<=(index-day).days<=365:continue
                raw=r['CURRENT_ICD10_LIST'] or '';codes=strict_list(raw)
                flags={f for f,prefix in DX.items() if codes and any(c.startswith(prefix) for c in codes)}
                if day is None:
                    undated[k].update(DX if codes is None else flags);continue
                if codes is None:
                    blocked[k].update(DX);qc['dated_missing_or_unparsed_rows']+=1
                else:
                    positives[k].update(flags)
                    if tokens(raw) is None:qc['dated_rows_recovered_by_complete_token_whitespace_parser']+=1
    return positives,blocked,undated,dict(qc)


def run(mapping_report,output,*,map_reviewed_labs=False):
    mapping_report,output=map(Path,(mapping_report,output))
    if any(not p.is_absolute() or p.is_symlink() for p in (mapping_report,output)):raise BuildError('absolute_nonsymlink_paths_required')
    audit=json.loads((mapping_report/'summary.json').read_text());am=json.loads((mapping_report/'manifest.json').read_text())
    if audit.get('version')!='comet_mapping_gaps_v1' or am.get('version')!=audit['version'] or audit.get('status')!='complete_mapping_gap_audit' or audit.get('counts_valid') is not True:raise BuildError('completed_mapping_audit_required')
    catalog=mapping_report/'restricted_target_lab_catalog.json'
    if digest(catalog)!=am['target_catalog_sha256']:raise BuildError('lab_catalog_changed')
    parent=Path(audit['baseline_report']);summary,manifest,checks=verify_parent(parent)
    if any(digest(Path(p))!=h for p,h in am['parent_checksums'].items()):raise BuildError('mapping_parent_changed')
    context=CachedContext(summary['cohort_report'],summary['candidate_cache'])
    if manifest['cohort_sha256']!=context.manifest['output_sha256']:raise BuildError('cohort_lineage_changed')
    for src in (mapping_report,parent,context.report,context.cache,*context.source_manifests):
        a,b=output.resolve(),src.resolve()
        if a==b or a in b.parents or b in a.parents:raise BuildError('output_source_overlap')
    for name in ('summary.json','manifest.json','restricted_target_lab_catalog.json'):checks[mapping_report/name]=digest(mapping_report/name)
    table=pq.read_table(parent/'baseline'/'restricted_baseline_staging.parquet');rows=table.to_pylist()
    bykey={r['patient_key']:r for r in rows}
    if len(bykey)!=len(rows) or set(bykey)!=set(context.anchors) or any(bykey[k]['index_date']!=r['candidate_order_day'] or bykey[k]['treatment_arm']!=r['candidate_arm'] for k,r in context.anchors.items()):raise BuildError('baseline_anchor_mismatch')
    retained,excluded=adult_rows(rows);keys={r['patient_key'] for r in retained}
    if not keys:raise BuildError('no_adult_range_candidates')
    os.umask(0o077);output.mkdir(parents=True,mode=0o700,exist_ok=False);start=time.monotonic()
    out=dict(version=VERSION if not map_reviewed_labs else 'comet_baseline_resolution_v2_mapped_labs',status='building',counts_valid=False,ready_for_mice=False,restricted_until_reviewed=True,
        source_report=str(parent),mapping_report=str(mapping_report),diagnosis_policy=POLICY,
        eligibility_change='Adult age18-120 at unchanged index; under18 excluded, absent/invalid age quarantined, not imputed. Other cohort rules unchanged. Not full COMET eligibility or phenotype validation.')
    atomic_json(output/'summary.json',out)
    try:
        positives,blocked,undated,qc=diagnosis_values(context,keys)
        transitions=Counter();states=pq.read_table(parent/'baseline'/'restricted_feature_status.parquet').to_pylist()
        states=[s for s in states if s['patient_key'] in keys];lookup={(s['patient_key'],s['feature']):s for s in states}
        features=[f for f in table.column_names if f not in ('patient_key','treatment_arm','index_date')]
        if len(features)!=32 or len(lookup)!=len(keys)*32 or len(states)!=len(lookup):raise BuildError('feature_status_alignment_failed')
        aux=[]
        for r in retained:
            k=r['patient_key']
            for f in DX:
                old=r[f];new,status=recorded_binary(f in positives[k],f in blocked[k]);r[f]=new
                lookup[k,f]['status']=status
                transitions[r['treatment_arm'],f,'null' if old is None else str(int(old)),'null' if new is None else str(new)]+=1
                aux.append(dict(patient_key=k,feature=f,undated_evidence_or_uncertainty=f in undated[k]))
        if map_reviewed_labs:
            from comet_reviewed_lab_map import extract, TARGETS
            values,statuses,lab_report=extract(parent,{k:context.anchors[k] for k in keys},output)
            for r in retained:
                for f in TARGETS:
                    r[f]=values[r['patient_key'],f]
                    lookup[r['patient_key'],f]['status']=statuses[r['patient_key'],f]
            out['lab_mapping']=lab_report
        groups=json.loads(catalog.read_text())['groups'];draft=[]
        for g in groups:
            target,decision=lab_draft(g)
            draft.append(dict(g,proposed_target=target,mapping_status=decision,approved=False,canonical_unit=None))
        atomic_json(output/'restricted_lab_mapping_draft.json',dict(restricted_keep_on_cluster=True,
            interpretation=('Legacy label triage; lab_mapping_report.json supersedes identity assignments, units remain unverified.' if map_reviewed_labs else 'Label triage only. No source-specific component identity or canonical unit approved. No lab values inserted into baseline.'),groups=draft))
        pq.write_table(pa.Table.from_pylist(retained,schema=table.schema),output/'restricted_baseline_resolution.parquet',compression='zstd')
        pq.write_table(pa.Table.from_pylist(states),output/'restricted_feature_status.parquet',compression='zstd')
        pq.write_table(pa.Table.from_pylist(aux),output/'restricted_undated_dx_auxiliary.parquet',compression='zstd')
        pq.write_table(pa.Table.from_pylist(excluded,schema=pa.schema([('patient_key',pa.string()),('arm',pa.string()),('reason',pa.string())])),output/'restricted_age_exclusions.parquet',compression='zstd')
        context.check_inputs()
        if any(digest(p)!=h for p,h in checks.items()):raise BuildError('inputs_changed')
        counts=Counter((r['treatment_arm'],f,lookup[r['patient_key'],f]['status'],r[f] is not None) for r in retained for f in features)
        outputs={p.name:digest(p) for p in output.iterdir() if p.name!='summary.json'}
        atomic_json(output/'manifest.json',dict(version=out['version'],script_sha256=digest(Path(__file__)),input_checksums={str(p):h for p,h in checks.items()},context_checksums={str(p):h for p,h in context.fingerprints.items()},outputs=outputs,diagnosis_policy=POLICY))
        out.update(status='complete_resolution_candidate',counts_valid=True,rows=len(retained),denominators=dict(Counter(r['treatment_arm'] for r in retained)),
            age_exclusions=[dict(arm=a,reason=s,patient_keys=n) for (a,s),n in sorted(Counter((r['arm'],r['reason']) for r in excluded).items())],
            diagnosis_transitions=[dict(arm=a,feature=f,before=b,after=v,patient_keys=n) for (a,f,b,v),n in sorted(transitions.items())],
            feature_status_counts=[dict(arm=a,feature=f,status=s,has_candidate_value=v,patient_keys=n) for (a,f,s,v),n in sorted(counts.items())],
            diagnosis_qc=qc,lab_mapping_draft_counts=dict(Counter(r['mapping_status'] for r in draft)),
            remaining=('Lab identities mapped to raw-scale candidates; canonical units remain unverified. ' if map_reviewed_labs else 'Lab component/specimen/unit map not approved. ')+'Vital units and availability remain unresolved. No imputation, propensity score, outcome or effect estimate. Recorded-diagnosis policy change is explicit and original baseline preserved.')
    except Exception as e:
        out.update(status='failed_counts_invalid',counts_valid=False,reason=str(e) if isinstance(e,BuildError) else type(e).__name__);raise
    finally:
        out['elapsed_seconds']=round(time.monotonic()-start,3);atomic_json(output/'summary.json',out)
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mapping-report',type=Path);p.add_argument('--map-reviewed-labs',action='store_true');p.add_argument('--project-root',type=Path,default=Path('/mnt/raid0/rbc58/ecg-tte'));p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    try:run(a.mapping_report or discover(a.project_root,'audits/comet-mapping-gaps-*/report/summary.json','comet_mapping_gaps_v1','complete_mapping_gap_audit'),a.output_dir,map_reviewed_labs=a.map_reviewed_labs)
    except Exception as e:print('Stopped: '+(str(e) if isinstance(e,BuildError) else type(e).__name__));return 1
    print('Completed resolution candidate. Review summary; units remain unverified and no MICE was run.');return 0

if __name__=='__main__':raise SystemExit(main())
