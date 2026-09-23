import contextlib
from datetime import date
import io
from pathlib import Path
import sys
import tempfile
import unittest

import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import test_build_comet_baseline_staging as T
import audit_comet_outcome_sources as A
from build_shared_tables import BuildError


class OutcomeSourceTests(unittest.TestCase):
    def test_missing_death_is_unknown_and_conflicts_are_separate(self):
        index = date(2024, 1, 1)
        self.assertEqual(A.death_state(set(), {'missing'}, 1, index), 'no_recorded_death_date')
        self.assertEqual(A.death_state(set(), set(), 0, index), 'no_patient_row')
        self.assertEqual(A.death_state({date(2024, 2, 1), date(2024, 3, 1)}, {'dated'}, 2, index), 'conflicting_death_dates')
        self.assertEqual(A.death_state({date(2023, 12, 1)}, {'dated'}, 1, index), 'death_before_index')
        self.assertEqual(A.death_state({date(2024, 2, 1)}, {'unparseable'}, 2, index), 'unparseable_death_date')

    def test_pooled_qc_does_not_make_endpoint_or_followup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            roster = root/'roster.parquet'
            pq.write_table(pa.table({'patient_key': ['A', 'B', 'C'],
                                     'candidate_order_day': [date(2024, 1, 1)]*3,
                                     'candidate_arm': ['one', 'two', 'one']}), roster)
            patients = pa.table({'PAT_MRN_ID': ['A', 'B', 'C', 'C'],
                                 'DEATH_DATE': ['2024-02-01', '', '2024-02-01', '2024-03-01'],
                                 'BIRTH_DATE': ['1980-01-01', '1980-01-01', '1980-01-01', '1980-01-01']})
            hospital_25 = pa.table({'PAT_MRN_ID': ['A', 'A', 'B'],
                                    'PAT_ENC_CSN_ID': ['X', 'X', 'Y'],
                                    'HOSP_ADMSN_DATE': ['2024-02-02', '2024-02-02', '2024-02-03'],
                                    'HOSP_DISCH_DATE': ['2024-02-04', '2024-02-04', '2024-02-02'],
                                    'INP_YN': ['1', '1', '1'], 'ED_YN': ['0']*3})
            hospital_26 = pa.table({'PAT_MRN_ID': ['A'], 'PAT_ENC_CSN_ID': ['X'],
                                    'HOSP_ADMSN_DATE': ['2024-02-02'], 'HOSP_DISCH_DATE': ['2024-02-04'],
                                    'INP_YN': ['1'], 'ED_YN': ['0']})
            outpatient = pa.table({'PAT_MRN_ID': ['B'], 'PAT_ENC_CSN_ID': ['O'], 'CONTACT_DATE': ['2024-01-02']})
            build = T.StagingTests().build
            snapshot = build(root, 'clinical', {
                A.PATIENTS: (patients, ['BIRTH_DATE', 'DEATH_DATE']),
                A.HOSPITAL[0]: (hospital_25, ['HOSP_ADMSN_DATE', 'HOSP_DISCH_DATE']),
                A.HOSPITAL[1]: (hospital_26, ['HOSP_ADMSN_DATE', 'HOSP_DISCH_DATE']),
                A.OUTPATIENT[0]: (outpatient, ['CONTACT_DATE']),
                A.OUTPATIENT[1]: (outpatient, ['CONTACT_DATE'])})
            with contextlib.redirect_stdout(io.StringIO()):
                result = A.run(roster, snapshot, root/'report')
            self.assertTrue(result['counts_valid'])
            self.assertEqual(result['death_date_states'], {
                'single_postindex_death_date': 1, 'no_recorded_death_date': 1,
                'conflicting_death_dates': 1})
            self.assertEqual(result['encounter_flags']['postdeath_encounter_rows_patients'], 1)
            self.assertEqual(result['encounter_flags']['discharge_after_death_rows_patients'], 1)
            self.assertEqual(result['encounter_flags']['duplicate_encounter_rows_patients'], 2)
            self.assertEqual(result['encounter_flags']['discharge_before_admission_rows_patients'], 1)
            self.assertNotIn('candidate_arm', result)
            self.assertNotIn('censor_day', result)
            private = pq.read_table(root/'report/restricted_patient_qc.parquet').to_pylist()
            self.assertEqual({r['patient_key']: r['death_date_state'] for r in private}['B'], 'no_recorded_death_date')
            self.assertEqual({r['patient_key']: r['postindex_inpatient_candidate_keys'] for r in private}['A'], 1)

    def test_refuses_existing_output_and_roster_overlap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            roster = root/'roster.parquet'
            roster.touch()
            snapshot = root/'snapshot'
            snapshot.mkdir()
            with self.assertRaises(BuildError):
                A.validate_paths(roster, snapshot, snapshot)
            with self.assertRaises(BuildError):
                A.validate_paths(roster, snapshot, root)
