import sys
from pathlib import Path
import json
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from summarize_comet_calipers import summarize,CUTOFFS

class GridSummaryTests(unittest.TestCase):
    def test_preserves_failed_and_missing_cutoffs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            p=root/'caliper-0.20/report';p.mkdir(parents=True)
            (p/'summary.json').write_text(json.dumps(dict(status='failed_comparison',counts_valid=False,reason='insufficient_caliper_matches_for_balance',assignment_objective={'matched_pairs':0})))
            s=summarize(root)
            self.assertEqual(len(s['runs']),3)
            self.assertEqual(s['status'],'grid_contains_incomplete_runs')
            self.assertEqual(s['runs'][0]['assignment_objective']['matched_pairs'],0)
            self.assertEqual(s['runs'][1]['status'],'missing_summary')
            self.assertTrue((root/'grid_summary.json').exists())

    def test_all_cutoffs_and_population_consistency(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            fields=('pairs','carvedilol_retention','metoprolol_retention','mean_abs_smd','max_abs_smd','features_ge_0_1','undefined_smd')
            for c in CUTOFFS:
                p=root/('caliper-'+c)/'report';p.mkdir(parents=True)
                (p/'summary.json').write_text(json.dumps(dict(version='comet_cosine_comparison_v4_caliper',status='complete_exploratory_comparison',counts_valid=True,common_rows=20,denominators={'c':12,'m':8},contract=dict(cosine_caliper=float(c),checkpoint_weights_sha256='synthetic'),methods={'cosine':[{f:1 for f in fields},{f:2 for f in fields}]})))
            s=summarize(root)
            self.assertEqual(s['status'],'complete_grid')
            self.assertEqual([r['caliper'] for r in s['runs']],[.2,.3,.4])
            self.assertEqual(s['runs'][0]['methods']['cosine']['pairs'],dict(min=1,max=2))
            p=root/'caliper-0.40/report/summary.json';v=json.loads(p.read_text());v['common_rows']=21;p.write_text(json.dumps(v))
            with self.assertRaisesRegex(ValueError,'population_or_checkpoint'):summarize(root)
if __name__=='__main__':unittest.main()
