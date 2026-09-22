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

    def test_r_summary_precision_roundtrip(self):
        import json
        import shutil
        import subprocess
        if not shutil.which('Rscript'):self.skipTest('Rscript unavailable')
        code = "cat(jsonlite::toJSON(list(caliper=0.23454321),auto_unbox=TRUE,digits=NA))"
        result=subprocess.run(['Rscript','--vanilla','-e',code],text=True,capture_output=True)
        if result.returncode:self.skipTest('R jsonlite unavailable')
        caliper=json.loads(result.stdout)['caliper']
        scores=[dict(patient_key='synthetic_a',logit='0'),dict(patient_key='synthetic_b',logit='0.23453')]
        pairs=[dict(carvedilol_key='synthetic_a',metoprolol_key='synthetic_b')]
        check_pairs(pairs,scores,caliper)
        with self.assertRaisesRegex(BuildError,'caliper'):
            check_pairs(pairs,scores,round(caliper,4))
        scores[1]['logit']='0.23455'
        with self.assertRaisesRegex(BuildError,'caliper'):
            check_pairs(pairs,scores,caliper)
        # Protect the engine writer from reintroducing default JSON rounding.
        engine=(Path(__file__).resolve().parents[1]/'scripts/comet_exploratory_psm.R').read_text()
        self.assertIn('pretty=TRUE,digits=NA',engine)
