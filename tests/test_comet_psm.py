import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_comet_exploratory_psm import check_pairs
from build_shared_tables import BuildError


class PairsTests(unittest.TestCase):
    def test_caliper_and_no_replacement(self):
        scores=[dict(patient_key='synthetic_a',logit='1'),dict(patient_key='synthetic_b',logit='1.1')]
        pairs=[dict(carvedilol_key='synthetic_a',metoprolol_key='synthetic_b')]
        check_pairs(pairs,scores,.1)
        with self.assertRaisesRegex(BuildError,'caliper'):check_pairs(pairs,scores,.05)
        with self.assertRaisesRegex(BuildError,'reused'):check_pairs(pairs*2,scores,.1)
