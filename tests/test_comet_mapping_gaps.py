import contextlib
from datetime import date
import io
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
import pyarrow as pa
import pyarrow.dataset as ds
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import audit_comet_mapping_gaps as G
import build_comet_cached_baseline as B
import test_comet_cached_baseline as T
from build_shared_tables import BuildError


class MappingTests(unittest.TestCase):
    def test_name_leads_are_discovery_not_approved_analytes(self):
        self.assertIn('creatinine',G.lab_leads('CREATININE, URINE',''))
        self.assertIn('hemoglobin',G.lab_leads('HEMOGLOBIN A1C',''))
        self.assertEqual(G.lab_leads('ALKALINE PHOSPHATASE','ALK'),set())
        self.assertEqual(G.lab_leads('POTASSIUM','K'),{'potassium'})
        self.assertEqual(G.code_reason('NULL'),'missing_icd10')
        self.assertEqual(G.code_reason('I48.91 / N18.3'),'unparsed_icd10')

    def test_reason_reconstruction_positive_override_and_future_exclusion(self):
        anchors={k:dict(candidate_arm='arm',candidate_order_day=date(2024,1,1)) for k in ('A','B')}
        data=ds.dataset(pa.table({'__patient_key':['A','A','B','B','B'],
            '__day_DX_DATE':[date(2023,12,1),date(2023,12,1),None,date(2023,12,1),date(2024,1,2)],
            'CURRENT_ICD10_LIST':['NULL','E11.9','N18.3','NULL','E11.9'],
            'CURRENT_ICD9_LIST':['250.00','','','250.00','']}))
        # In-memory data has no files; production datasets are Parquet.
        class Table:
            files=[]
            schema=data.schema
            def scanner(self,**kw):return data.scanner(**kw)
        context=SimpleNamespace(anchors=anchors,core=Path('/core/snapshot'),dx=Path('/extra/snapshot'),open=lambda *a:Table())
        baseline={k:{f:None for f in G.DX} for k in anchors};baseline['A']['diabetes']=1
        with contextlib.redirect_stdout(io.StringIO()):result=G.explain_dx(context,baseline)
        reasons={(r['feature'],r['reason']) for r in result['reason_counts']}
        self.assertIn(('ckd','missing_date__parseable_icd10__icd9_missing'),reasons)
        self.assertIn(('diabetes','prior365__missing_icd10__icd9_present'),reasons)
        null_diabetes=next(r for r in result['feature_counts'] if r['feature']=='diabetes' and r['status']=='recorded_evidence_unassessable')
        self.assertEqual(null_diabetes['patient_keys'],1)
        baseline['B']['diabetes']=0
        with contextlib.redirect_stdout(io.StringIO()),self.assertRaisesRegex(BuildError,'reconstruction_differs'):G.explain_dx(context,baseline)

    def test_complete_audit_uses_saved_extract_and_patient_union(self):
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            p=Path(tmp);report,cache=T.CachedBaselineTests().fixture(p)
            B.run(report,cache,p/'baseline')
            result=G.run(p/'baseline',p/'audit')
            self.assertEqual(result['status'],'complete_mapping_gap_audit')
            self.assertFalse(result['baseline_changed']);self.assertFalse(result['ready_for_mice'])
            self.assertEqual(result['laboratory']['rows_reviewed'],3)
            self.assertEqual(result['laboratory']['any_lab_union'],[{'arm':'carvedilol_candidate','patient_keys':1}])
            self.assertTrue(result['diagnosis']['reconstruction_matches_saved_values'])
            with (p/'baseline'/'labs'/'outpatient_labs.parquet').open('ab') as f:f.write(b'altered')
            with self.assertRaisesRegex(BuildError,'parent_artifact_changed'):G.run(p/'baseline',p/'bad')
            self.assertFalse((p/'bad').exists())
