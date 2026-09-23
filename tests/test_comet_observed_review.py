import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from review_comet_representation_balance import combine,stats,BuildError
class ReviewTests(unittest.TestCase):
    def test_observed_counts_and_signed_values(self):
        s=dict(methods={'cosine':[dict(imputation=1,pairs=4)]},denominators=dict(carvedilol_candidate=10,metoprolol_tartrate_candidate=8))
        c=[dict(method='cosine',imputation='1',feature='lvef',smd_pre='0.8',smd_post='0.6',post_carvedilol_mean='35',post_metoprolol_mean='50'),dict(method='cosine',imputation='1',feature='missing:lvef',smd_post='0.1')]
        o=[dict(method='cosine',imputation='1',feature='lvef',smd_pre='-0.9',smd_post='-0.7',pre_observed_carvedilol='6',pre_observed_metoprolol='5',post_observed_carvedilol='2',post_observed_metoprolol='3')]
        r=combine(c,o,s)[0]
        self.assertEqual(r['observed_post_abs_smd']['median'],.7)
        self.assertEqual(r['observed_post_signed_smd']['median'],-.7)
        self.assertEqual(r['post_observed_fraction_carvedilol']['median'],.5)
        o[0]['post_observed_carvedilol']='5'
        with self.assertRaises(BuildError):combine(c,o,s)
    def test_undefined_is_not_zero(self):
        self.assertIsNone(stats(['NA','nan','inf'])['median'])
        self.assertEqual(stats(['NA','0.4'])['defined'],1)
if __name__=='__main__':unittest.main()
