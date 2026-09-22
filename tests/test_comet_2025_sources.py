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
import build_comet_2025_sources as D
import audit_comet_2025_sources as A
import build_shared_tables as B

class SourcesTests(unittest.TestCase):
    def test_selection_excludes_damaged_labs(self):
        def header(root,relative):
            return dict(status='header_candidate',delimiter='tab',schema_sha256=D.DX_HASH if '_DX.' in relative else D.SCHEMAS['labs_2025'],columns=['PAT_MRN_ID','DX_DATE','RESULT_DATE'])
        with patch.object(D,'inspect',side_effect=header):
            dx=D.specs(Path('/synthetic'),'diagnoses');labs=D.specs(Path('/synthetic'),'outpatient-labs')
        self.assertEqual(len(dx),2);self.assertEqual(len(labs),1)
        self.assertTrue(labs[0]['path'].endswith('_Outpatient_Enc_Labs.txt'))
        self.assertFalse(labs[0]['terminal_empty'])
        with patch.object(D,'inspect',return_value={}):
            with self.assertRaises(B.BuildError):D.specs(Path('/synthetic'),'diagnoses')
    def test_fixed_cohort_no_future_evidence_or_exclusion(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);build=T.StagingTests().build
            diagnoses=pa.table({'PAT_MRN_ID':['A','A'],'DX_DATE':['2023-12-01','2024-02-01'],'PAT_ENC_CSN_ID':['E','E'],'CURRENT_ICD10_LIST':['I50.3','I50.2'],'DX_NAME':['diastolic failure','HF']})
            dx=build(p,'dx',{n:(diagnoses,['DX_DATE']) for n in ('hospital_diagnoses','outpatient_diagnoses')})
            lab=build(p,'lab',{'outpatient_labs':(pa.table({'PAT_MRN_ID':['A','A'],'RESULT_DATE':['2023-12-01','2024-01-01'],'COMPONENT_ID':['C','F'],'COMPONENT_NAME':['synthetic','future'],'BASE_NAME':['x','y']}),['RESULT_DATE'])})
            clinical=build(p,'clinical',{'Data_2025_04_03_hosp_enc':(pa.table({'PAT_MRN_ID':['A'],'PAT_ENC_CSN_ID':['E'],'HOSP_ADMSN_DATE':['2023-12-01'],'INP_YN':['1'],'ED_YN':['0']}),['HOSP_ADMSN_DATE'])})
            cohort=p/'cohort';cohort.mkdir();cp=cohort/'restricted_broad_candidates.parquet'
            pq.write_table(pa.table({'patient_key':['A'],'candidate_arm':['arm'],'candidate_order_day':[date(2024,1,1)]}),cp)
            with patch.object(A,'verify',return_value=({},dict(output_sha256=B.digest(cp)))),contextlib.redirect_stdout(io.StringIO()):s=A.run(cohort,dx,lab,clinical,p/'out')
            self.assertEqual(s['denominators'],{'arm':1})
            flags={x['flag'] for x in s['patients']}
            self.assertIn('prior365_exclusion_signal',flags);self.assertNotIn('prior365_systolic',flags)
            self.assertEqual(s['lab_catalog_combinations'],1)
            self.assertEqual(s['inpatient_linkage'][0]['keys_matching_any_diagnosis'],1)
            self.assertEqual(pq.read_table(cp).num_rows,1)
