from datetime import date
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import pyarrow as pa
import pyarrow.parquet as pq
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import audit_comet_broad_cohort as A
import build_shared_tables as B

class BroadTests(unittest.TestCase):
    def test_history_groups_are_mutually_exclusive(self):
        groups={A.history_group(p,u) for p in (0,3) for u in (0,2)}
        self.assertEqual(len(groups),4)
    def test_general_code_or_low_ef_and_no_ties(self):
        r={'candidate_arm':'carvedilol_candidate','DX_DATE_prior_hf_evidence':False}
        self.assertTrue(A.selected(r,'gt1_lt40',set()));self.assertFalse(A.selected(r,'eq40',set()))
        r['DX_DATE_prior_hf_evidence']=True
        self.assertTrue(A.selected(r,'missing',set()))
        self.assertFalse(A.selected(r,'gt1_lt40',{'combined'}))
        self.assertFalse(A.selected(r,'gt1_lt40',{'hfpef_mention'}))
        r['candidate_arm']='competing_arms_same_day';self.assertFalse(A.selected(r,'gt1_lt40',set()))
    def test_end_to_end_retains_history_without_excluding_and_no_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=root/'raw';raw.mkdir();core=root/'core'
            t=pa.table({'MRN':['A','B','B','C'],'EchoDate':['2024-01-01','2023-12-01','2024-01-01','2024-01-01'],
                        'EF':pa.array([39.,30.,None,40.],type=pa.float64())})
            src=raw/'echo.parquet';pq.write_table(t,src)
            spec=dict(id='echo_studies',path=str(src),format='parquet',schema_fields=[(f.name,str(f.type)) for f in t.schema],
                      expected_rows=4,key='MRN',dates=['EchoDate'],terminal_empty=False)
            specs=[spec]
            for name in ('hospital_diagnoses','outpatient_diagnoses'):
                dx=pa.table({'PAT_MRN_ID':['A','C','C'],'DX_DATE':['2024-01-01','2024-02-01','2024-03-01'],
                    'CURRENT_ICD10_LIST':['I50.32']*3,'DX_NAME':['Diastolic HF']*3})
                path=raw/(name+'.parquet');pq.write_table(dx,path)
                specs.append(dict(id=name,path=str(path),format='parquet',schema_fields=[(f.name,str(f.type)) for f in dx.schema],
                    expected_rows=3,key='PAT_MRN_ID',dates=['DX_DATE'],terminal_empty=False))
            with contextlib.redirect_stdout(io.StringIO()):B.build(specs,core)
            report=root/'comet-candidates-test'/'report';report.mkdir(parents=True)
            candidate=report/'restricted_candidates.parquet'
            pq.write_table(pa.table({'patient_key':['A','B','C'],'candidate_arm':['carvedilol_candidate']*3,
                'candidate_order_day':[date(2024,2,1)]*3,'DX_DATE_prior_hf_evidence':[False,False,True],
                'prior_365d_family_order_records':[3,0,3],'undated_family_order_records':[2,0,2]}),candidate)
            h=B.digest(core/'manifest.json')
            (report/'summary.json').write_text(json.dumps(dict(version='comet_candidates_v1',status='complete_provisional_candidates',counts_valid=True,candidate_patient_keys=3,core_manifest_sha256=h)))
            (report/'restricted_manifest.json').write_text(json.dumps(dict(version='comet_candidates_v1',rows=3,core_manifest_sha256=h,core_snapshot=str(core),candidate_sha256=B.digest(candidate))))
            with contextlib.redirect_stdout(io.StringIO()):r=A.run(report,root/'out')
            self.assertEqual(r['selected_candidate_keys'],1)
            self.assertEqual(r['before_exclusions_by_arm']['carvedilol_candidate'],2)
            self.assertEqual(r['removed_by_exclusions_by_arm']['carvedilol_candidate'],1)
            self.assertEqual(sum(x['patient_keys'] for x in r['history_groups']),1)
            self.assertEqual(sum(x['patient_keys'] for x in r['calendar_history_groups']),1)
            self.assertEqual(sum(x['patient_keys'] for x in r['evidence_groups']),1)
            rows=pq.read_table(root/'out'/'restricted_broad_candidates.parquet').to_pylist()
            self.assertEqual({x['patient_key'] for x in rows},{'C'})
            self.assertEqual(rows[0]['prior_365d_family_order_records'],3)
            self.assertEqual(rows[0]['broad_history_group'],'prior_365d_found_and_undated')
            with self.assertRaises(FileExistsError):A.run(report,root/'out')

if __name__=='__main__':unittest.main()
