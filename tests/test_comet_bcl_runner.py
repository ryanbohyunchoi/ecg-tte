import json,sys,tempfile,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_comet_bcl_smoke import validate_vectors
from build_shared_tables import BuildError
class RunnerTests(unittest.TestCase):
    def test_vectors_and_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            (p/'shard_00000_index.csv').write_text('row,fileID,error\n0,synthetic/a,\n1,synthetic/b,\n')
            (p/'embedding_config.json').write_text(json.dumps(dict(embed_dim=3,num_rows=2)))
            np.save(p/'shard_00000.npy',np.ones((2,3),dtype=np.float32))
            self.assertEqual(validate_vectors(p,['synthetic/a','synthetic/b'])['rows'],2)
            with self.assertRaises(BuildError):validate_vectors(p,['synthetic/b','synthetic/a'])
            a=np.ones((2,3),dtype=np.float32);a[0,0]=np.nan;np.save(p/'shard_00000.npy',a)
            with self.assertRaises(BuildError):validate_vectors(p,['synthetic/a','synthetic/b'])
            a[0]=0;np.save(p/'shard_00000.npy',a)
            with self.assertRaises(BuildError):validate_vectors(p,['synthetic/a','synthetic/b'])
