import sys
from pathlib import Path
import tempfile
import unittest
import pyarrow as pa
import pyarrow.parquet as pq
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from inspect_embedding_assets import inspect


class LeadTests(unittest.TestCase):
    def test_footer_only_no_values_or_directory_listing(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'metadata.parquet'
            pq.write_table(pa.table({'key':['synthetic_private_marker'],'day':['2020-01-01']}),p)
            result=inspect(p)
            self.assertEqual(result['rows'],1)
            self.assertNotIn('synthetic_private_marker',str(result))
            self.assertEqual(inspect(Path(tmp))['status'],'directory_exists_no_listing')
            self.assertEqual(inspect(Path(tmp)/'absent')['status'],'not_found')
