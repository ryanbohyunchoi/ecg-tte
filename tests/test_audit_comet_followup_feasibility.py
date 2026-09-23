import contextlib
from datetime import date
import io
from pathlib import Path
import sys
import tempfile
import unittest

import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import audit_comet_followup_feasibility as F
import audit_comet_outcome_sources as A
import test_build_comet_baseline_staging as T


class FollowupFeasibilityTests(unittest.TestCase):
    def test_lag_bins(self):
        self.assertEqual(F.lag_bin(-1),'before_index')
        self.assertEqual(F.lag_bin(0),'index_day')
        self.assertEqual(F.lag_bin(365),'days181_365')
        self.assertEqual(F.lag_bin(366),'days366_730')
        self.assertEqual(F.lag_bin(731),'over730')

    def test_pooled_landmarks_are_not_censoring(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);roster=root/'roster.parquet'
            pq.write_table(pa.table({'patient_key':['A','B','C'],'candidate_order_day':[date(2024,1,1)]*3}),roster)
            patients=pa.table({'PAT_MRN_ID':['A','B','C'],'DEATH_DATE':['2024-04-01','','2023-12-01']})
            hosp=pa.table({'PAT_MRN_ID':['A','A','B'],'PAT_ENC_CSN_ID':['H1','H2','H3'],
                'HOSP_ADMSN_DATE':['2024-02-01','2025-02-01','2024-01-10'],'INP_YN':['1','1','0']})
            out=pa.table({'PAT_MRN_ID':['B'],'PAT_ENC_CSN_ID':['O1'],'CONTACT_DATE':['2024-07-01']})
            build=T.StagingTests().build
            snapshot=build(root,'clinical',{
                A.PATIENTS:(patients,['DEATH_DATE']),
                A.HOSPITAL[0]:(hosp,['HOSP_ADMSN_DATE']),A.HOSPITAL[1]:(hosp.slice(2,1),['HOSP_ADMSN_DATE']),
                A.OUTPATIENT[0]:(out,['CONTACT_DATE']),A.OUTPATIENT[1]:(out,['CONTACT_DATE'])})
            with contextlib.redirect_stdout(io.StringIO()):s=F.run(roster,snapshot,root/'report')
            self.assertTrue(s['counts_valid']);self.assertEqual(s['death_lag_bins']['days91_180'],1)
            self.assertEqual(s['death_qc']['no_recorded_death_date'],1)
            self.assertEqual(s['death_qc']['death_on_or_before_index'],1)
            self.assertEqual(s['first_inpatient_lag_bins']['days31_90'],1)
            self.assertEqual(s['candidate_inpatient_keys'],2)
            self.assertEqual(s['horizon_encounter_signals']['any_encounter_at_or_after_365d'],1)
            self.assertNotIn('censor_day',s);self.assertNotIn('candidate_arm',s)
