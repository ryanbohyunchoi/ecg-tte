import contextlib
from datetime import date
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pyarrow as pa
import pyarrow.parquet as pq
import test_build_comet_baseline_staging as T
import reassess_comet_diagnoses as R
import reuse_comet_hospital_labs as L
import build_shared_tables as B
import candidate_event_cache as C

class ReassessmentTests(unittest.TestCase):
    def test_expanded_sources_enter_remove_and_keep_index_fixed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);builder=T.StagingTests().build
            def dx(keys,codes,days):return pa.table({'PAT_MRN_ID':keys,'DX_DATE':days,'CURRENT_ICD10_LIST':codes,'DX_NAME':['']*len(keys)})
            olddx=dx(['A'],['I50.2'],['2023-12-01']);newdx=dx(['A','B','C'],['I50.3','I50.2','I50.2'],['2023-12-01','2023-12-01','2024-02-01'])
            core=builder(p,'core',dict(echo_studies=(pa.table({'PAT_MRN_ID':['A','B','C'],'EchoDate':['2023-12-01']*3,'EF':[30.,40.,40.]}),['EchoDate']),hospital_diagnoses=(olddx,['DX_DATE']),outpatient_diagnoses=(olddx,['DX_DATE'])))
            extra=builder(p,'extra',{n:(newdx,['DX_DATE']) for n in ('hospital_diagnoses','outpatient_diagnoses')})
            report=p/'candidates'/'report';report.mkdir(parents=True);cp=report/'restricted_candidates.parquet'
            rows=pa.table({'patient_key':['A','B','C'],'candidate_arm':['carvedilol_candidate']*3,'candidate_order_day':[date(2024,1,1)]*3,'DX_DATE_prior_hf_evidence':[True,False,False],'prior_365d_family_order_records':[0]*3,'undated_family_order_records':[0]*3})
            pq.write_table(rows,cp);h=B.digest(core/'manifest.json')
            (report/'summary.json').write_text(json.dumps(dict(version='comet_candidates_v1',status='complete_provisional_candidates',counts_valid=True,candidate_patient_keys=3,core_manifest_sha256=h)))
            (report/'restricted_manifest.json').write_text(json.dumps(dict(version='comet_candidates_v1',rows=3,core_manifest_sha256=h,core_snapshot=str(core),candidate_sha256=B.digest(cp))))
            previous=p/'previous';previous.mkdir();oldpath=previous/'restricted_broad_candidates.parquet';pq.write_table(rows.slice(0,1),oldpath)
            with patch('audit_comet_beta_history.verify',return_value=({},dict(output_sha256=B.digest(oldpath)))),contextlib.redirect_stdout(io.StringIO()):s=R.run(report,extra,previous,p/'out')
            self.assertEqual(s['selected_candidate_keys'],1)
            self.assertEqual({r['transition']:r['patient_keys'] for r in s['transitions']},{'entered':1,'removed':1,'not_selected':1})
            result=pq.read_table(p/'out'/'restricted_broad_candidates.parquet').to_pylist()
            self.assertEqual(result[0]['patient_key'],'B');self.assertEqual(result[0]['candidate_order_day'],date(2024,1,1))
            with patch('audit_comet_beta_history.verify',return_value=({},dict(output_sha256=B.digest(oldpath)))),contextlib.redirect_stdout(io.StringIO()):
                C.build_cache(report,[core,extra],p/'cache')
                cached=R.run(report,extra,previous,p/'cached',candidate_cache=p/'cache')
            self.assertEqual(cached['transitions'],s['transitions'])
            self.assertEqual(cached['evidence_groups'],s['evidence_groups'])
            self.assertEqual(pq.read_table(p/'cached'/'restricted_broad_candidates.parquet').to_pylist(),result)

    def test_limited_reuse_verifies_raw_and_preserves_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);raw=p/'Data-2025-04-03';raw.mkdir();specs=[]
            for i,name in enumerate(L.IDS,1):
                src=raw/f'CarDS_2435227_Hosp_Enc_Labs_{i}.txt';t=pa.table({'PAT_MRN_ID':['A']});pq.write_table(t,src)
                specs.append(dict(id=name,path=str(src),format='parquet',schema_fields=[('PAT_MRN_ID','string')],expected_rows=1,key='PAT_MRN_ID',dates=[],terminal_empty=False))
            old=p/'old'
            with contextlib.redirect_stdout(io.StringIO()):m=B.build(specs,old)
            m['status']='failed';B.atomic_json(old/'manifest.json',m);before=B.digest(old/'manifest.json')
            with contextlib.redirect_stdout(io.StringIO()):s=L.run(old,p/'new')
            self.assertEqual(s['status'],'complete');self.assertEqual(B.digest(old/'manifest.json'),before)
            self.assertEqual(set(s['stages']),set(L.IDS));self.assertEqual(B.open_table(p/'new',L.IDS[0]).count_rows(),1)
            with Path(specs[0]['path']).open('ab') as f:f.write(b'changed')
            with contextlib.redirect_stdout(io.StringIO()),self.assertRaises(B.BuildError):L.run(old,p/'bad')
            self.assertEqual(json.loads((p/'bad'/'manifest.json').read_text())['status'],'failed')
