import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_comet_bcl_smoke import choose
from build_shared_tables import BuildError

class SmokeTests(unittest.TestCase):
    def test_strata_and_determinism(self):
        rows=[dict(status='selected_for_smoke',treatment_arm=a,format_250hz=b,fileID=f'folder/{a}{b}{i:02}') for a in ('a','b') for b in ('True','False') for i in range(10)]
        self.assertEqual(len(choose(rows)),32)
        self.assertEqual(len(choose(rows,True)),40)
        self.assertEqual(choose(rows),choose(list(reversed(rows))))
        rows[0]['format_250hz']='unknown'
        with self.assertRaises(BuildError):choose(rows)
    def test_unsafe_id(self):
        with self.assertRaises(BuildError):choose([dict(status='selected_for_smoke',treatment_arm='a',format_250hz='True',fileID='../x')])
