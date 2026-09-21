#!/usr/bin/env python3
"""Read-only completion/integrity check; no patient values are printed."""
import argparse
import hashlib
import json
from pathlib import Path


def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(4194304),b''):h.update(chunk)
    return h.hexdigest()


def check(run):
    report=run/'report'
    result={'run_directory':str(run),'check':'not_checked'}
    if run.is_symlink() or report.is_symlink():
        result['check']='symlink_not_checked';return result
    summary=report/'summary.json'
    if not summary.is_file():
        result['check']='no_saved_summary';return result
    try:
        s=json.loads(summary.read_text())
        statuses={'building','complete_provisional_candidates','failed_candidates_invalid'}
        status=s.get('status')
        result['saved_status']=status if status in statuses else 'unrecognized'
        if status!='complete_provisional_candidates' or s.get('counts_valid') is not True:
            result['check']='not_complete_process_state_unknown';return result
        manifest=report/'restricted_manifest.json';candidate=report/'restricted_candidates.parquet'
        if not manifest.is_file() or not candidate.is_file():
            result['check']='completion_artifact_missing';return result
        if manifest.is_symlink() or candidate.is_symlink():
            result['check']='symlink_not_checked';return result
        m=json.loads(manifest.read_text())
        if s.get('version')!='comet_candidates_v1' or m.get('version')!='comet_candidates_v1':
            result['check']='version_mismatch';return result
        n=s.get('candidate_patient_keys')
        if type(n) is not int or n<0 or m.get('rows')!=n:
            result['check']='row_count_mismatch';return result
        if m.get('core_manifest_sha256')!=s.get('core_manifest_sha256'):
            result['check']='source_lineage_mismatch';return result
        if sha256(candidate)!=m.get('candidate_sha256'):
            result['check']='candidate_hash_mismatch';return result
        import pyarrow.parquet as pq
        with pq.ParquetFile(candidate) as pf:
            if pf.metadata.num_rows!=n:
                result['check']='parquet_row_count_mismatch';return result
        result.update(check='complete_candidate_artifact_verified',candidate_patient_keys=n,
                      final_eligible_cohort=False)
    except Exception as exc:
        result.update(check='check_failed_no_raw_error_export',error_type=type(exc).__name__)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--audit-root',type=Path,required=True)
    a=p.parse_args()
    if not a.audit_root.is_absolute() or not a.audit_root.is_dir():
        print('Audit root must be an existing absolute directory.');return 1
    runs=sorted(p for p in a.audit_root.glob('comet-candidates-*') if p.is_dir())
    print(json.dumps(dict(restricted_until_reviewed=True,
        interpretation='Saved status and candidate artifact checks only; building does not prove a live process. No run is launched.',
        matched_run_directories=len(runs),runs=[check(p) for p in runs]),indent=2))
    return 0

if __name__=='__main__':raise SystemExit(main())
