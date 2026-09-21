from datetime import date, timedelta
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
import audit_comet_beta_history as A
import build_shared_tables as B

class BetaHistoryTests(unittest.TestCase):
    def test_name_leads_are_not_mapping(self):
        self.assertEqual(A.classify(('ATENOLOL / chlorthalidone',))[0],'named_generic')
        self.assertEqual(A.classify(('timolol ophthalmic',))[1],('timolol',))
        self.assertEqual(A.classify(('Toprol XL',))[0],'unresolved_name_lead')
        self.assertEqual(A.classify(('unknownolol',))[0],'unresolved_name_lead')
        self.assertEqual(A.classify(('furosemide',))[0],'no_name_match')
    def test_time_boundaries(self):
        index=date(2024,1,1)
        for lag,expected in [(0,'same_day'),(1,'prior365'),(365,'prior365'),(366,'outside_window'),(-1,'outside_window')]:
            self.assertEqual(A.relation(index-timedelta(days=lag),index),expected)
        self.assertEqual(A.relation(None,index),'undated')
    def fixture(self,root):
        core=root/'core';raw=root/'raw';raw.mkdir();src=raw/'med.parquet'
        names=['carvedilol','bisoprolol','Toprol XL','atenolol','metoprolol tartrate','timolol','carvedilol']
        t=pa.table({'PAT_MRN_ID':['A','A','A','A','B','B','B'],
            'ORDER_INST':['2024-01-01','2023-12-01','NULL','2024-01-02','2024-01-01','2024-01-01','2022-01-01'],
            'MEDICATION_NAME':names,'GENERIC_NAME':['']*7,'SIMPLE_GENERIC':['']*7,
            'MEDICATION_ID':[str(x) for x in range(7)],'MEDICATION_ROUTE':['oral']*5+['ophthalmic','oral'],
            'ORDERING_MODE':['Outpatient']*7,'ORDER_CLASS':['Normal']*7})
        pq.write_table(t,src)
        spec=dict(id='medication_orders',path=str(src),format='parquet',schema_fields=[(f.name,str(f.type)) for f in t.schema],expected_rows=7,key='PAT_MRN_ID',dates=['ORDER_INST'],terminal_empty=False)
        with contextlib.redirect_stdout(io.StringIO()):B.build([spec],core)
        report=root/'comet-broad-test'/'report';report.mkdir(parents=True)
        p=report/'restricted_broad_candidates.parquet'
        pq.write_table(pa.table({'patient_key':['A','B'],'candidate_arm':['carvedilol_candidate','metoprolol_tartrate_candidate'],
            'candidate_order_day':[date(2024,1,1)]*2,'candidate_order_source_rows':[[1],[5]]}),p)
        s=dict(version='comet_broad_exploratory_v2',status='complete_exploratory_cohort_audit',counts_valid=True,selected_candidate_keys=2,core_snapshot=str(core))
        m=dict(version=s['version'],output_sha256=B.digest(p),rows=2,core_manifest_sha256=B.digest(core/'manifest.json'))
        (report/'summary.json').write_text(json.dumps(s));(report/'restricted_manifest.json').write_text(json.dumps(m))
        return report
    def test_full_scan_preserves_index_and_separates_uncertainty(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);report=self.fixture(root);self.assertEqual(A.discover(root),report)
            original=B.digest(report/'restricted_broad_candidates.parquet')
            r=A.run(report,root/'out')
            self.assertEqual(r['index_rows_verified'],2)
            self.assertEqual(sum(x['patient_keys'] for x in r['history_groups']),2)
            groups={x['arm']:x for x in r['history_groups']}
            self.assertTrue(groups['carvedilol_candidate']['prior365_generic_found'])
            self.assertTrue(groups['carvedilol_candidate']['unresolved_prior_or_undated_lead'])
            self.assertFalse(groups['metoprolol_tartrate_candidate']['prior365_generic_found'])
            self.assertTrue(groups['metoprolol_tartrate_candidate']['other_same_day_lead'])
            self.assertIsNone(r['qualified_new_user_patients'])
            self.assertEqual(original,B.digest(report/'restricted_broad_candidates.parquet'))
            self.assertEqual(sum(x['records'] for x in r['record_counts']),5)
            with self.assertRaises(FileExistsError):A.run(report,root/'out')
    def test_missing_index_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);report=self.fixture(root);p=report/'restricted_broad_candidates.parquet'
            rows=pq.read_table(p).to_pylist();rows[0]['candidate_order_source_rows']=[100]
            pq.write_table(pa.Table.from_pylist(rows),p)
            m=json.loads((report/'restricted_manifest.json').read_text());m['output_sha256']=B.digest(p)
            (report/'restricted_manifest.json').write_text(json.dumps(m))
            with self.assertRaisesRegex(B.BuildError,'index_source_rows_missing'):A.run(report,root/'out')
            self.assertFalse(json.loads((root/'out'/'summary.json').read_text())['counts_valid'])
            self.assertFalse((root/'out'/'restricted_medication_mapping.json').exists())
    def test_changed_cohort_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);report=self.fixture(root)
            with (report/'restricted_broad_candidates.parquet').open('ab') as f:f.write(b'changed')
            with self.assertRaisesRegex(B.BuildError,'cohort_hash_mismatch'):A.run(report,root/'out')
            self.assertFalse((root/'out').exists())

if __name__=='__main__':unittest.main()
