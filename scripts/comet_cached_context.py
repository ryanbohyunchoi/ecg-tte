"""Verified expanded COMET cohort and explicitly bound cached source deliveries."""
from collections import Counter
from datetime import date
import json
from pathlib import Path
import pyarrow.parquet as pq
from build_shared_tables import BuildError, digest
from candidate_event_cache import open_cached, VERSION
from audit_comet_clinical_baseline import IDS

COHORT_VERSION='comet_expanded_dx_reassessment_v1'
LAB_IDS={'Data_2025_04_03_hosp_enc_labs_1','Data_2025_04_03_hosp_enc_labs_2'}


class CachedContext:
    def __init__(self,report,cache):
        self.report,self.cache=map(Path,(report,cache))
        if any(not p.is_absolute() or p.is_symlink() for p in (self.report,self.cache)):
            raise BuildError('absolute_nonsymlink_paths_required')
        self.fingerprints={};self.tables={}
        def read(path):
            self.fingerprints[path]=digest(path)
            return json.loads(path.read_text())
        self.summary=read(self.report/'summary.json')
        self.manifest=read(self.report/'restricted_manifest.json')
        s,m=self.summary,self.manifest
        if s.get('version')!=COHORT_VERSION or m.get('version')!=COHORT_VERSION or s.get('status')!='complete_expanded_dx_reassessment' or s.get('counts_valid') is not True:
            raise BuildError('completed_expanded_cohort_required')
        for filename,hashfield in [('restricted_broad_candidates.parquet','output_sha256'),('restricted_transitions.parquet','transitions_sha256')]:
            path=self.report/filename
            if path.is_symlink() or digest(path)!=m.get(hashfield):raise BuildError('cohort_artifact_changed')
            self.fingerprints[path]=m[hashfield]
        cp=self.report/'restricted_broad_candidates.parquet'
        with pq.ParquetFile(cp) as f:
            if not 0<f.metadata.num_rows<=1000000 or f.metadata.num_rows!=m.get('rows') or f.metadata.num_rows!=s.get('selected_candidate_keys'):raise BuildError('cohort_row_mismatch')
            self.roster=f.read(columns=['patient_key','candidate_arm','candidate_order_day']).to_pylist()
        self.anchors={r['patient_key']:r for r in self.roster}
        if len(self.anchors)!=len(self.roster) or any(not isinstance(k,str) or not k or not isinstance(r['candidate_order_day'],date) or r['candidate_arm'] not in {'carvedilol_candidate','metoprolol_tartrate_candidate'} for k,r in self.anchors.items()):raise BuildError('invalid_cohort_anchors')
        if dict(Counter(r['candidate_arm'] for r in self.roster))!=s.get('by_arm'):raise BuildError('cohort_arm_counts_mismatch')
        cm=read(self.cache/'manifest.json')
        if cm.get('version')!=VERSION or cm.get('status')!='complete' or cm.get('candidate_sha256')!=m.get('candidate_sha256'):raise BuildError('cache_cohort_lineage_mismatch')
        self.cache_manifest=cm
        sources={Path(e['source_snapshot']) for e in cm['tables']}
        self.source_manifests={}
        for src in sources:
            if not src.is_absolute() or src.is_symlink():raise BuildError('invalid_source_path')
            sm=read(src/'manifest.json');self.source_manifests[src]=sm
            if sm.get('status')!='complete' or sm.get('version')!='shared_sources_v1':raise BuildError('incomplete_source')
            if any(e['source_manifest_sha256']!=self.fingerprints[src/'manifest.json'] for e in cm['tables'] if Path(e['source_snapshot'])==src):raise BuildError('cache_source_changed')
        self.core=Path(s['core_snapshot']);self.dx=Path(s['additional_dx_snapshot'])
        if self.fingerprints.get(self.core/'manifest.json')!=m.get('core_manifest_sha256') or self.fingerprints.get(self.dx/'manifest.json')!=m.get('additional_dx_manifest_sha256'):raise BuildError('cohort_source_lineage_mismatch')
        def one(ids):
            paths=[p for p,sm in self.source_manifests.items() if set(sm['stages'])==ids]
            if len(paths)!=1:raise BuildError('ambiguous_or_missing_source_role')
            return paths[0]
        self.clinical=one(IDS);self.outpatient_labs=one({'outpatient_labs'});self.hospital_labs=one(LAB_IDS)
        if len({self.core,self.dx,self.clinical,self.outpatient_labs,self.hospital_labs})!=5 or len(sources)!=5:raise BuildError('unexpected_source_roles')
        # Cross-check retained anchors against their immutable original medication roster.
        candidate=Path(cm['candidate_report'])/'restricted_candidates.parquet'
        if digest(candidate)!=m['candidate_sha256']:raise BuildError('original_candidates_changed')
        self.fingerprints[candidate]=m['candidate_sha256']
        original=pq.read_table(candidate,columns=['patient_key','candidate_arm','candidate_order_day']).to_pylist()
        bykey={r['patient_key']:r for r in original}
        if len(bykey)!=len(original) or any(bykey.get(k)!=r for k,r in self.anchors.items()):raise BuildError('cohort_anchor_changed')
        transitions=pq.read_table(self.report/'restricted_transitions.parquet',columns=['patient_key','expanded_selected']).to_pylist()
        if len({r['patient_key'] for r in transitions})!=len(transitions) or {r['patient_key'] for r in transitions if r['expanded_selected']}!=set(self.anchors):raise BuildError('transition_roster_mismatch')

    def verify(self,report):
        if Path(report)!=self.report:raise BuildError('context_cohort_mismatch')
        self.check_inputs()
        return self.summary,self.manifest

    def open(self,snapshot,name):
        key=(Path(snapshot),name)
        if key not in self.tables:
            self.tables[key]=open_cached(key[0],name,self.cache,required_keys=self.anchors)
        return self.tables[key]

    def check_inputs(self):
        if any(digest(p)!=h for p,h in self.fingerprints.items()):raise BuildError('context_input_changed')
