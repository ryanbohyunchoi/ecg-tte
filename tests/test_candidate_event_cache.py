import contextlib
from datetime import date
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import candidate_event_cache as C
import build_shared_tables as B
from build_comet_candidates import records
import test_build_comet_baseline_staging as T


class CacheTests(unittest.TestCase):
    def test_exact_key_filter_preserves_dates_duplicates_nulls_and_projection(self):
        t=ds.dataset(pa.table({'__patient_key':['A','A',' A','B',None],
            'day':[date(1900,1,1),None,date(2020,1,1),None,None],
            'value':['old','undated','space','other','null']}))
        self.assertEqual(list(records(t,['value'],patient_keys={'A'})),[{'value':'old'},{'value':'undated'}])
        self.assertEqual(list(records(t,['value'],patient_keys=set())),[])

    def test_cache_integrity_population_and_empty_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);report=p/'candidate'/'report';report.mkdir(parents=True)
            pq.write_table(pa.table({'patient_key':['A']}),report/'restricted_candidates.parquet')
            source=T.StagingTests().build(p,'source',{
                'events':(pa.table({'PAT_MRN_ID':['A','A','B'],'DAY':['1900-01-01',None,'2024-01-01'],'VALUE':['old','undated','other']}),['DAY']),
                'empty':(pa.table({'PAT_MRN_ID':['B']}),[])})
            with patch.object(C,'check',return_value={'check':'complete_candidate_artifact_verified'}),contextlib.redirect_stdout(io.StringIO()):
                state=C.build_cache(report,[source],p/'cache')
            self.assertEqual(state['status'],'complete')
            table=C.open_cached(source,'events',p/'cache',{'A'})
            self.assertEqual(table.to_table()['VALUE'].to_pylist(),['old','undated'])
            self.assertEqual(C.open_cached(source,'empty',p/'cache',{'A'}).count_rows(),0)
            with self.assertRaisesRegex(B.BuildError,'population_not_superset'):C.open_cached(source,'events',p/'cache',{'B'})
            part=p/'cache'/state['tables'][0]['parts'][0]['file']
            with part.open('ab') as f:f.write(b'corruption')
            with self.assertRaisesRegex(B.BuildError,'cache_part_changed'):C.open_cached(source,'events',p/'cache',{'A'})
            manifest=source/'manifest.json';manifest.write_text(manifest.read_text()+'\n')
            with self.assertRaisesRegex(B.BuildError,'source_not_found_or_changed'):C.open_cached(source,'events',p/'cache',{'A'})
            self.assertIsInstance(json.loads((p/'cache'/'summary.json').read_text())['tables'][0]['parts'],int)
