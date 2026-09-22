import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from datetime import date
from types import SimpleNamespace
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import resolve_comet_baseline_gaps as R
import audit_comet_mapping_gaps as G
import build_comet_cached_baseline as B
import test_comet_cached_baseline as T


class ResolutionTests(unittest.TestCase):
    def test_parser_requires_whole_valid_code_list(self):
        self.assertEqual(R.strict_list(' I48.91 N18.3;E11.9 '),{'I4891','N183','E119'})
        for raw in ('no I48.91','I48.91 / N18.3','I48.91,','I48.91;;N18.3','NULL',''):
            self.assertIsNone(R.strict_list(raw))

    def test_age_quarantine_and_exact_lab_draft(self):
        rows=[dict(patient_key=str(i),treatment_arm='arm',age_at_index=a) for i,a in enumerate([17,18,120,121,None,-1,float('nan')])]
        kept,excluded=R.adult_rows(rows)
        self.assertEqual([r['age_at_index'] for r in kept],[18,120]);self.assertEqual(len(excluded),5)
        self.assertEqual(R.lab_draft({'component_name':'HEMOGLOBIN A1C'}),(None,'name_requires_review'))
        self.assertEqual(R.lab_draft({'component_name':'CREATININE','specimen_type':'URINE'}),('creatinine','non_target_specimen_review'))
        self.assertEqual(R.lab_draft({'component_name':'CREATININE'}),('creatinine','exact_name_candidate_requires_specimen_and_unit_review'))

    def test_versioned_run_preserves_source_and_keeps_labs_unapproved(self):
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            p=Path(tmp);report,cache=T.CachedBaselineTests().fixture(p)
            B.run(report,cache,p/'baseline');G.run(p/'baseline',p/'mapping')
            before=(p/'baseline'/'baseline'/'restricted_baseline_staging.parquet').read_bytes()
            s=R.run(p/'mapping',p/'resolution')
            self.assertEqual(s['status'],'complete_resolution_candidate');self.assertFalse(s['ready_for_mice'])
            self.assertEqual(s['rows'],2)
            r=pq.read_table(p/'resolution'/'restricted_baseline_resolution.parquet').to_pylist()
            self.assertEqual(r[0]['diabetes'],1);self.assertIsNone(r[0]['creatinine'])
            self.assertEqual(before,(p/'baseline'/'baseline'/'restricted_baseline_staging.parquet').read_bytes())
            self.assertEqual(sum(v['patient_keys'] for v in s['diagnosis_transitions']),18)

    def test_undated_auxiliary_is_separate_and_dated_errors_stay_null(self):
        data=ds.dataset(pa.table({'__patient_key':['A','B','B','C','C'],
            '__day_DX_DATE':[None,date(2023,12,1),date(2024,2,1),date(2023,12,1),date(2023,12,2)],
            'CURRENT_ICD10_LIST':['N18.3','bad','N18.3','bad','I48.91']}))
        class Table:
            files=[]
            schema=data.schema
            def scanner(self,**kw):return data.scanner(**kw)
        ctx=SimpleNamespace(core=Path('/core/snapshot'),dx=Path('/extra/snapshot'),
            anchors={k:{'candidate_order_day':date(2024,1,1)} for k in 'ABC'},open=lambda *args:Table())
        with contextlib.redirect_stdout(io.StringIO()):pos,blocked,aux,qc=R.diagnosis_values(ctx,set('ABC'))
        self.assertIn('ckd',aux['A']);self.assertFalse(blocked['A']);self.assertFalse(pos['A'])
        self.assertIn('ckd',blocked['B']);self.assertFalse(pos['B'])
        self.assertEqual(R.recorded_binary('atrial_fibrillation' in pos['C'],'atrial_fibrillation' in blocked['C']),(1,'recorded_positive'))
