import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from compare_comet_clmbr import cosine_pairs, BuildError

class CosineTests(unittest.TestCase):
    def test_exact_directions_and_order_invariance(self):
        keys=['a','b','c','d'];arms=['carvedilol_candidate']*2+['metoprolol_tartrate_candidate']*2
        x=np.array([[2,0],[0,3],[5,0],[0,7]])
        result=cosine_pairs(keys,arms,x)
        self.assertEqual({(r['carvedilol_key'],r['metoprolol_key']) for r in result},{('a','c'),('b','d')})
        order=[3,1,0,2]
        self.assertEqual(result,cosine_pairs([keys[i] for i in order],[arms[i] for i in order],x[order]))
        self.assertTrue(all(r['cosine_distance']==0 for r in result))
    def test_invalid_vectors(self):
        for x in ([[0,0],[1,0],[1,0],[0,1]],[[float('nan'),0],[1,0],[1,0],[0,1]]):
            with self.assertRaises(BuildError):cosine_pairs(['a','b','c','d'],['carvedilol_candidate']*2+['metoprolol_tartrate_candidate']*2,x)
    def test_ties_no_reuse(self):
        r=cosine_pairs(['b','a','d','c','e'],['carvedilol_candidate']*3+['metoprolol_tartrate_candidate']*2,np.ones((5,2)))
        self.assertEqual([p['metoprolol_key'] for p in r],['c','e'])
        self.assertEqual(len({p['carvedilol_key'] for p in r}),2)

    def test_v2_embedding_dependent_selection_and_orientation(self):
        keys=['c1','c2','c3','c4','m1','m2']
        arms=['carvedilol_candidate']*4+['metoprolol_tartrate_candidate']*2
        x=np.array([[1,0],[0,1],[-1,0],[0,-1],[1,0],[0,1]])
        before=cosine_pairs(keys,arms,x,metoprolol_anchor=True)
        self.assertEqual({r['carvedilol_key'] for r in before},{'c1','c2'})
        self.assertEqual({r['metoprolol_key'] for r in before},{'m1','m2'})
        changed=x.copy();changed[4:]*=-1
        after=cosine_pairs(keys,arms,changed,metoprolol_anchor=True)
        self.assertEqual({r['carvedilol_key'] for r in after},{'c3','c4'})
        # Original contract remains reproducible and embedding-independent in membership.
        old=lambda v:{r['carvedilol_key'] for r in cosine_pairs(keys,arms,v)}
        self.assertEqual(old(x),old(changed))
        order=[5,3,0,2,4,1]
        self.assertEqual(before,cosine_pairs([keys[j] for j in order],[arms[j] for j in order],x[order],metoprolol_anchor=True))
        tied=cosine_pairs(keys,arms,np.ones((6,2)),metoprolol_anchor=True)
        self.assertEqual([r['carvedilol_key'] for r in tied],['c1','c2'])
        self.assertTrue(all(r['cosine_distance']==0 for r in before))

    def test_v2_refuses_inverted_arm_sizes(self):
        with self.assertRaisesRegex(BuildError,'metoprolol_anchor_exceeds'):
            cosine_pairs(['c','m1','m2'],['carvedilol_candidate']+['metoprolol_tartrate_candidate']*2,np.ones((3,2)),metoprolol_anchor=True)

    def test_global_optimum_against_exhaustive_assignments(self):
        from itertools import permutations
        keys=['c0','c1','c2','m0','m1'];arms=['carvedilol_candidate']*3+['metoprolol_tartrate_candidate']*2
        rng=np.random.default_rng(44)
        strict_improvements=0
        for _ in range(20):
            x=rng.normal(size=(5,4));x/=np.linalg.norm(x,axis=1)[:,None]
            result=cosine_pairs(keys,arms,x,optimal=True)
            optimum=min(sum(1-np.clip(x[3+i]@x[j],-1,1) for i,j in enumerate(p)) for p in permutations(range(3),2))
            total=sum(r['cosine_distance'] for r in result)
            self.assertAlmostEqual(total,optimum,places=12)
            greedy=sum(r['cosine_distance'] for r in cosine_pairs(keys,arms,x,metoprolol_anchor=True))
            self.assertLessEqual(total,greedy+1e-12)
            strict_improvements+=total<greedy-1e-8
            self.assertEqual(len({r['carvedilol_key'] for r in result}),2)
            self.assertEqual({r['metoprolol_key'] for r in result},{'m0','m1'})
            order=[4,2,0,3,1]
            self.assertEqual(result,cosine_pairs([keys[i] for i in order],[arms[i] for i in order],x[order],optimal=True))
        self.assertGreater(strict_improvements,0)


class ComparisonIntegration(unittest.TestCase):
    def test_synthetic_pipeline_and_input_tamper(self):
        import tempfile, json, shutil, subprocess
        from unittest.mock import patch
        import pyarrow as pa
        import pyarrow.parquet as pq
        from compare_comet_clmbr import run, digest, CONTRACT, verified
        rscript=shutil.which('Rscript')
        if not rscript:self.skipTest('Rscript unavailable')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);mice=root/'mice';emb=root/'emb';base=root/'base'
            for p in (mice,emb,base):p.mkdir()
            def dump(p,x):p.write_text(json.dumps(x))
            rng=np.random.default_rng(831);n=200;rows=[];vectors=[]
            for i in range(n):
                arm='carvedilol_candidate' if i<120 else 'metoprolol_tartrate_candidate'
                r=dict(patient_key=f'synthetic_{i}',treatment_arm=arm,index_date='2020-01-01',age_at_index=float(rng.normal(60,10)),recorded_sex='Female' if i%2 else 'Male',lvef=float(rng.uniform(15,65)))
                rows.append(r);vectors.append(dict(patient_key=r['patient_key'],treatment_arm=arm,index_date=r['index_date'],embedding=rng.normal(size=768).tolist()))
            columns=['treatment_arm','age_at_index','recorded_sex','lvef']
            dump(mice/'model_spec.json',dict(m=1,columns=columns,numeric=['age_at_index','lvef'],binary=[]))
            dump(mice/'restricted_row_keys.json',[r['patient_key'] for r in rows])
            dump(mice/'restricted_missingness_mask.json',[{f:False for f in columns} for _ in rows])
            pq.write_table(pa.Table.from_pylist(rows),base/'restricted_cleaned_baseline.parquet')
            pq.write_table(pa.Table.from_pylist(rows),mice/'restricted_completed_01.parquet')
            subprocess.run([rscript,'--vanilla','-e','a<-commandArgs(TRUE);saveRDS(list(mean=array(rep(1,100),c(1,50,2),dimnames=list("lvef",NULL,NULL))),a[1])',str(mice/'chain_traces.rds')],check=True,capture_output=True)
            dump(mice/'summary.json',dict(version='comet_mice_pilot_v2_ordered_bp',source_report=str(base)))
            dump(mice/'manifest.json',dict(outputs={p.name:digest(p) for p in mice.iterdir() if p.name!='summary.json'}))
            pq.write_table(pa.Table.from_pylist(vectors),emb/'restricted_embeddings_part-000.parquet')
            pq.write_table(pa.Table.from_pylist([dict(patient_key=r['patient_key'],status='encoded') for r in rows]),emb/'restricted_patient_status.parquet')
            dump(emb/'summary.json',dict(status='complete_embeddings_requires_review',counts_valid=True,limit=0,numeric_mode='code-only',max_tokens=4096,totals={'encoded':n}))
            dump(emb/'manifest.json',dict(model_sha256={'model.safetensors':CONTRACT['checkpoint_weights_sha256']},outputs={p.name:digest(p) for p in emb.iterdir() if p.name!='summary.json'}))
            with patch('compare_comet_clmbr.review',return_value=dict(startup_abi_warning_detected=False,bp_inconsistent_patient_imputation_rows=0)):
                result=run(emb,mice,root/'out',rscript,optimal=True)
            self.assertTrue(result['counts_valid']);self.assertEqual(result['common_rows'],n)
            self.assertEqual(result['methods']['cosine'][0]['pairs'],80)
            self.assertEqual(result['version'],'comet_cosine_comparison_v3_global_optimal')
            self.assertTrue((root/'out/comparison_love_plots.pdf').is_file())
            (emb/'restricted_embeddings_part-000.parquet').write_bytes(b'changed')
            with self.assertRaises(BuildError):verified(emb)

class MaskContractTests(unittest.TestCase):
    def test_row_mask_validation_and_subset(self):
        from compare_comet_clmbr import validate_mask
        rows=[dict(treatment_arm='a',bp=None),dict(treatment_arm='b',bp=120)]
        mask=[dict(treatment_arm=False,bp=True),dict(treatment_arm=False,bp=False)]
        validate_mask(mask,rows,['treatment_arm','bp'])
        validate_mask([mask[1]],[rows[1]],['treatment_arm','bp'])
        for bad in ({'bp':[True,False]},mask[:1],[dict(treatment_arm=False,bp=1),mask[1]],
                    [dict(treatment_arm=False,bp=False),mask[1]]):
            with self.assertRaises(BuildError):validate_mask(bad,rows,['treatment_arm','bp'])

    def test_safe_frames_exclude_exception_contents(self):
        from compare_comet_clmbr import validate_mask,safe_error_frames
        try:validate_mask('synthetic_private_value',[],[])
        except BuildError as e:
            frames=safe_error_frames(e)
        self.assertTrue(frames)
        self.assertNotIn('synthetic_private_value',str(frames))
        self.assertEqual(set(frames[0]),{'module','function','line'})

if __name__=='__main__':unittest.main()
