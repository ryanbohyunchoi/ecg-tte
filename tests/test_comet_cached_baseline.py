import contextlib
from datetime import date
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import build_comet_cached_baseline as R
import comet_cached_context as C
import candidate_event_cache as E
import build_shared_tables as B
import test_build_comet_baseline_staging as T


class CachedBaselineTests(unittest.TestCase):
    def test_patient_specific_date_window(self):
        table=ds.dataset(pa.table({'__patient_key':['A']*5+['B','X'],
            '__day_RESULT_DATE':[date(2023,10,3),date(2023,10,2),date(2024,1,1),date(2024,1,2),None,date(2024,1,1),date(2023,12,1)]}))
        anchors={'A':{'candidate_order_day':date(2024,1,1)},'B':{'candidate_order_day':date(2024,2,1)}}
        rows=[r for batch in R.baseline_lab_batches(table,anchors,table.schema.names) for r in batch.to_pylist()]
        self.assertEqual([(r['__patient_key'],r['__day_RESULT_DATE']) for r in rows],[('A',date(2023,10,3)),('B',date(2024,1,1))])

    def fixture(self,p):
        build=T.StagingTests().build
        def dx(code):return pa.table({'PAT_MRN_ID':['A'],'DX_DATE':['2023-12-01'],'CALC_DX_DATE':['2023-12-01'],'CURRENT_ICD10_LIST':[code],'CURRENT_ICD9_LIST':[''],'PAT_ENC_CSN_ID':['H']})
        core=build(p,'core',{'echo_studies':(pa.table({'PAT_MRN_ID':['A'],'EchoDate':['2023-12-01'],'EF':[30.]}),['EchoDate']),
            'medication_orders':(pa.table({'PAT_MRN_ID':['A'],'ORDER_INST':['2023-12-01'],'MEDICATION_NAME':['lisinopril'],'GENERIC_NAME':[''],'SIMPLE_GENERIC':['']}),['ORDER_INST']),
            'hospital_diagnoses':(dx('I50.2'),['DX_DATE','CALC_DX_DATE']),'outpatient_diagnoses':(dx('I50.2'),['DX_DATE','CALC_DX_DATE'])})
        extra=build(p,'extra',{n:(dx('E11.9'),['DX_DATE','CALC_DX_DATE']) for n in ('hospital_diagnoses','outpatient_diagnoses')})
        tables={}
        for name in C.IDS:
            if name.endswith('_patients'):
                tables[name]=(pa.table({'PAT_MRN_ID':['A','B'],'BIRTH_DATE':['1980-01-01','1970-01-01'],'SEX_C':['1','2'],'SEX':['Female','Male']}),['BIRTH_DATE'])
            elif name.endswith('_vitals'):
                tables[name]=(pa.table({'PAT_MRN_ID':['A'],'RECORDED_TIME':['2023-12-01 12:00'],'PAT_ENC_CSN_ID':['V'],'FLO_MEAS_ID':['5'],'FLO_MEAS_NAME':['BLOOD PRESSURE'],'DISP_NAME':['BP'],'MEAS_VALUE':['120/80'],'UNIT':['NULL']}),['RECORDED_TIME'])
            elif name.endswith('_hosp_enc'):
                tables[name]=(pa.table({'PAT_MRN_ID':['A'],'HOSP_ADMSN_DATE':['2023-12-01'],'PAT_ENC_CSN_ID':['H'],'INP_YN':['1'],'ED_YN':['0']}),['HOSP_ADMSN_DATE'])
            else:
                tables[name]=(pa.table({'PAT_MRN_ID':['A'],'CONTACT_DATE':['2023-12-02'],'PAT_ENC_CSN_ID':['O']}),['CONTACT_DATE'])
        clinical=build(p,'clinical',tables)
        labs=pa.table({'PAT_MRN_ID':['A','A','B'],'RESULT_DATE':['2023-12-01','2024-01-01',None],'RESULT_TIME':['2023-12-01 12:00','2024-01-01 12:00','NULL'],'COMPONENT_ID':['1']*3,'COMPONENT_NAME':['CREATININE']*3,'BASE_NAME':['CREAT']*3,'ORD_VALUE':['1.2','9.0','2.0'],'ORD_NUM_VALUE':['1.2','9.0','2.0']})
        outlab=build(p,'outlab',{'outpatient_labs':(labs,['RESULT_DATE'])})
        hosp=build(p,'hosp',{n:(labs,['RESULT_DATE']) for n in C.LAB_IDS})
        orig=p/'original'/'report';orig.mkdir(parents=True)
        roster=pa.table({'patient_key':['A','B'],'candidate_arm':['carvedilol_candidate','metoprolol_tartrate_candidate'],'candidate_order_day':[date(2024,1,1)]*2})
        pq.write_table(roster,orig/'restricted_candidates.parquet');ch=B.digest(orig/'restricted_candidates.parquet')
        report=p/'report';report.mkdir();pq.write_table(roster,report/'restricted_broad_candidates.parquet')
        pq.write_table(pa.table({'patient_key':['A','B'],'expanded_selected':[True,True]}),report/'restricted_transitions.parquet')
        B.atomic_json(report/'summary.json',dict(version=C.COHORT_VERSION,status='complete_expanded_dx_reassessment',counts_valid=True,selected_candidate_keys=2,by_arm={'carvedilol_candidate':1,'metoprolol_tartrate_candidate':1},core_snapshot=str(core),additional_dx_snapshot=str(extra)))
        B.atomic_json(report/'restricted_manifest.json',dict(version=C.COHORT_VERSION,rows=2,output_sha256=B.digest(report/'restricted_broad_candidates.parquet'),transitions_sha256=B.digest(report/'restricted_transitions.parquet'),candidate_sha256=ch,core_manifest_sha256=B.digest(core/'manifest.json'),additional_dx_manifest_sha256=B.digest(extra/'manifest.json')))
        with patch.object(E,'check',return_value={'check':'complete_candidate_artifact_verified'}):E.build_cache(orig,[core,extra,clinical,outlab,hosp],p/'cache')
        return report,p/'cache'

    def test_complete_run_preserves_roster_unions_dx_and_restricts_labs(self):
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            p=Path(tmp);report,cache=self.fixture(p)
            s=R.run(report,cache,p/'out')
            self.assertEqual(s['status'],'complete_cached_baseline_staging');self.assertFalse(s['ready_for_mice'])
            rows=pq.read_table(p/'out'/'baseline'/'restricted_baseline_staging.parquet').to_pylist()
            self.assertEqual([r['patient_key'] for r in rows],['A','B'])
            self.assertEqual(rows[0]['diabetes'],1);self.assertEqual(rows[1]['diabetes'],0)
            self.assertEqual(rows[0]['hospital_admissions'],1);self.assertEqual(rows[1]['hospital_admissions'],0)
            self.assertEqual(rows[0]['sbp'],120);self.assertIsNone(rows[0]['creatinine'])
            lab=pq.read_table(p/'out'/'labs'/'outpatient_labs.parquet').to_pylist()
            self.assertEqual(len(lab),1);self.assertEqual(lab[0]['ORD_VALUE'],'1.2')
            self.assertEqual(sum(x['patient_keys'] for x in s['feature_status_counts']),64)
            with self.assertRaises(FileExistsError):R.run(report,cache,p/'out')
            with (report/'restricted_transitions.parquet').open('ab') as f:f.write(b'x')
            with self.assertRaisesRegex(B.BuildError,'cohort_artifact_changed'):C.CachedContext(report,cache)

    def test_changed_source_fails_before_output(self):
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            p=Path(tmp);report,cache=self.fixture(p)
            src=p/'extra'/'manifest.json';src.write_text(src.read_text()+'\n')
            with self.assertRaisesRegex(B.BuildError,'cache_source_changed'):R.run(report,cache,p/'out')
            self.assertFalse((p/'out').exists())
