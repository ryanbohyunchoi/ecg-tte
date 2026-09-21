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
import audit_comet_eligibility as A
import build_shared_tables as B

class EligibilityTests(unittest.TestCase):
    def test_calendar_months_and_code_boundaries(self):
        self.assertEqual(A.two_months_before(date(2024,4,30)),date(2024,2,29))
        self.assertEqual(A.two_months_before(date(2024,1,31)),date(2023,11,30))
        self.assertEqual(A.code_leads('I21.9; I63.9'),('mi','stroke'))
        self.assertEqual(A.code_leads('I25.2'),())
        self.assertEqual(A.code_leads('I21.9;garbage'),('unresolved_code',))
        self.assertEqual(A.code_leads('NULL'),('missing_code',))
    def test_medication_windows_and_no_continuity_claim(self):
        self.assertIn('beta_prior14',A.medication_signals(('metoprolol',),14))
        self.assertNotIn('beta_prior14',A.medication_signals(('metoprolol',),15))
        self.assertEqual(A.medication_signals(('metoprolol',),-1),[])
        self.assertEqual(A.medication_signals(('Toprol',),None),['unresolved_beta_undated'])
        self.assertEqual(A.medication_signals(('timolol eye drops',),0),['beta_same_day'])
        self.assertIn('ace_prior28to365',A.medication_signals(('lisinopril',),28))
        self.assertNotIn('ace_prior28to365',A.medication_signals(('lisinopril',),27))
    def test_echo_boundary_stale_and_conflict(self):
        index=date(2024,4,30);e=dict(day=date(2024,4,1),values={35.})
        self.assertEqual(A.ef_screen(e,index,35),'meets_numeric_screen')
        e['values']={40.};self.assertEqual(A.ef_screen(e,index,40),'fails_numeric_screen')
        e['values']={30.,None};self.assertEqual(A.ef_screen(e,index,35),'unknown')
        e=dict(day=date(2020,1,1),values={30.});self.assertEqual(A.ef_screen(e,index,35),'unknown')
    def fixture(self,root):
        raw=root/'raw';raw.mkdir();core=root/'core';specs=[]
        tables={
          'medication_orders':(pa.table({'PAT_MRN_ID':['A','A','A','B'], 'ORDER_INST':['2024-04-30','2024-04-16','2024-05-01','NULL'],
             'MEDICATION_NAME':['carvedilol','bisoprolol','atenolol','Toprol'],'GENERIC_NAME':['']*4,'SIMPLE_GENERIC':['']*4}), 'PAT_MRN_ID',['ORDER_INST']),
          'echo_studies':(pa.table({'MRN':['A','B','B','A'],'EchoDate':['2024-04-01','2024-03-01','2024-04-01','2024-04-30'],
             'EF':pa.array([35.,30.,None,20.],type=pa.float64())}),'MRN',['EchoDate']),
          'hospital_diagnoses':(pa.table({'PAT_MRN_ID':['A','B','A'],'DX_DATE':['2024-02-29','2024-04-30','2024-02-28'],
             'CURRENT_ICD10_LIST':['I21.9','I63.9','I63.9']}),'PAT_MRN_ID',['DX_DATE']),
          'outpatient_diagnoses':(pa.table({'PAT_MRN_ID':['A','B'],'DX_DATE':['2024-05-01','NULL'],'CURRENT_ICD10_LIST':['I63.9','I21.9']}),'PAT_MRN_ID',['DX_DATE'])}
        for name,(t,key,dates) in tables.items():
            path=raw/(name+'.parquet');pq.write_table(t,path)
            specs.append(dict(id=name,path=str(path),format='parquet',schema_fields=[(f.name,str(f.type)) for f in t.schema],expected_rows=t.num_rows,key=key,dates=dates,terminal_empty=False))
        with contextlib.redirect_stdout(io.StringIO()):B.build(specs,core)
        report=root/'report';report.mkdir();p=report/'restricted_broad_candidates.parquet'
        pq.write_table(pa.table({'patient_key':['A','B'],'candidate_arm':['carvedilol_candidate','metoprolol_tartrate_candidate'],
             'candidate_order_day':[date(2024,4,30)]*2}),p)
        s=dict(version='comet_broad_exploratory_v2',status='complete_exploratory_cohort_audit',counts_valid=True,selected_candidate_keys=2,core_snapshot=str(core))
        (report/'summary.json').write_text(json.dumps(s))
        (report/'restricted_manifest.json').write_text(json.dumps(dict(version=s['version'],rows=2,core_manifest_sha256=B.digest(core/'manifest.json'),output_sha256=B.digest(p))))
        return report,core
    def test_integration_no_future_fallback_or_false_eligibility(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);report,core=self.fixture(root);before=B.digest(report/'restricted_broad_candidates.parquet')
            with contextlib.redirect_stdout(io.StringIO()) as stdout:r=A.run(report,root/'out')
            self.assertTrue(r['counts_valid']);self.assertIsNone(r['clinical_eligible_patients'])
            self.assertEqual(before,B.digest(report/'restricted_broad_candidates.parquet'))
            screens={(x['arm'],x['screen']):x['status'] for x in r['numeric_screens']}
            self.assertEqual(screens['carvedilol_candidate','ef_le35'],'meets_numeric_screen')
            self.assertEqual(screens['metoprolol_tartrate_candidate','ef_le35'],'unknown')
            self.assertEqual(sum(x['patient_keys'] for x in r['overlapping_evidence_groups']),2)
            for c in r['criterion_register']:
                for arm,n in r['denominators'].items():self.assertEqual(c['by_arm'][arm],dict(meets=0,fails=0,unknown=n))
            evidence=pq.read_table(root/'out'/'restricted_evidence.parquet').to_pylist()
            self.assertTrue(any(x['signal']=='mi_recent' and x['patient_key']=='A' for x in evidence))
            self.assertFalse(any(x['signal']=='stroke_recent' for x in evidence))
            self.assertTrue(any(x['signal']=='mi_undated' for x in evidence))
            self.assertFalse(any(x['evidence_day'] and x['evidence_day']>date(2024,4,30) for x in evidence))
            self.assertNotIn('2024-04',stdout.getvalue())
            with self.assertRaises(FileExistsError):A.run(report,root/'out')
    def test_failed_core_not_bypassed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);report,core=self.fixture(root)
            p=core/'manifest.json';m=json.loads(p.read_text());m['status']='failed';p.write_text(json.dumps(m))
            p=report/'restricted_manifest.json';m=json.loads(p.read_text());m['core_manifest_sha256']=B.digest(core/'manifest.json');p.write_text(json.dumps(m))
            with self.assertRaises(B.BuildError):A.run(report,root/'out')
            s=json.loads((root/'out'/'summary.json').read_text());self.assertFalse(s['counts_valid'])
            self.assertFalse((root/'out'/'restricted_evidence.parquet').exists())

if __name__=='__main__':unittest.main()
