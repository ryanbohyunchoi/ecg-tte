import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from prepare_comet_mice import clean
from build_shared_tables import BuildError


class CleaningTests(unittest.TestCase):
    def test_only_agreed_cells_change_and_people_retained(self):
        rows = [dict(patient_key='synthetic1', dbp=0., bmi=.5, sbp=120., creatinine=12.),
                dict(patient_key='synthetic2', dbp=80., bmi=1200., sbp=130.),
                dict(patient_key='synthetic3', dbp=None, bmi=29., sbp=None)]
        result, log = clean(rows)
        self.assertEqual(len(result), 3)
        self.assertEqual(len(log), 3)
        self.assertIsNone(result[0]['dbp'])
        self.assertIsNone(result[0]['bmi'])
        self.assertIsNone(result[1]['bmi'])
        self.assertEqual(result[0]['sbp'], 120.)
        self.assertEqual(result[0]['creatinine'], 12.)
        self.assertEqual(rows[0]['dbp'], 0.)
        self.assertEqual(result[2], rows[2])

    def test_no_silent_threshold_expansion(self):
        rows = [dict(patient_key='synthetic', dbp=1., bmi=1000.)]
        self.assertEqual(clean(rows), (rows, []))
        with self.assertRaises(BuildError):
            clean([dict(patient_key='synthetic', dbp=float('nan'), bmi=20.)])
