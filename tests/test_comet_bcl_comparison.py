import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_comet_bcl_comparison import link_vectors
from build_shared_tables import BuildError
class LinkTests(unittest.TestCase):
    def test_link_reorder_and_cutoff(self):
        base=[dict(patient_key=k,treatment_arm=a,index_date='2020-02-01') for k,a in [('p1','carvedilol_candidate'),('p2','metoprolol_tartrate_candidate')]]
        links=[dict(**b,status='selected_for_smoke',fileID='synthetic/'+b['patient_key'],ecg_date='2020-01-31') for b in base]
        rows=link_vectors(links,['synthetic/p2','synthetic/p1'],np.ones((2,256)),base)
        self.assertEqual([r['patient_key'] for r in rows],['p2','p1'])
        links[0]['ecg_date']='2020-02-01'
        with self.assertRaises(BuildError):link_vectors(links,['synthetic/p1','synthetic/p2'],np.ones((2,256)),base)
    def test_duplicate_and_missing(self):
        b=[dict(patient_key='p',treatment_arm='carvedilol_candidate',index_date='2020-02-01')]
        l=[dict(**b[0],status='selected_for_smoke',fileID='synthetic/x',ecg_date='2020-01-31')]
        with self.assertRaises(BuildError):link_vectors(l,['synthetic/x','synthetic/x'],np.ones((2,256)),b)
        with self.assertRaises(BuildError):link_vectors(l,['synthetic/x'],np.ones((0,256)),b)
