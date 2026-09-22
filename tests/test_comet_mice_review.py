import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from review_comet_mice_pilot import summarize_ac,bp_review


class ReviewTests(unittest.TestCase):
    def test_ac_excludes_complete_and_nonfinite(self):
        rows=[{'vrb':'x','.it':str(i),'ac':str(i/10)} for i in range(1,8)]
        rows += [{'vrb':'x','.it':'8','ac':'NA'},{'vrb':'complete','.it':'9','ac':'0.9'}]
        result=summarize_ac(rows,{'x','missing'})
        self.assertEqual(result[0]['finite_iterations'],0)
        self.assertEqual(result[1]['final_ac'],.7)
        self.assertAlmostEqual(result[1]['last5_mean_abs_ac'],.5)

    def test_bp_provenance_and_repeated_person(self):
        original=[dict(patient_key='synthetic',sbp=120,dbp=None)]
        completed=[dict(treatment_arm='arm',sbp=120,dbp=130)]
        one,keys1=bp_review(original,completed,1)
        two,keys2=bp_review(original,completed,2)
        self.assertEqual(one[0]['basis'],'dbp_imputed')
        self.assertEqual(one[0]['rows']+two[0]['rows'],2)
        self.assertEqual(len(keys1|keys2),1)
        self.assertEqual(bp_review(original,[dict(treatment_arm='arm',sbp=120,dbp=80)],1),([],set()))
