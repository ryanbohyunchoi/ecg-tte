import sys
from pathlib import Path
from datetime import date
import tempfile
import unittest
import pyarrow as pa
import pyarrow.parquet as pq
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_comet_embedding_coverage import audit, day

class CoverageTests(unittest.TestCase):
    def test_timing_collision_duplicates_aliases_and_privacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); vectors=root/'vectors'; vectors.mkdir()
            metadata=root/'meta.parquet'; cache=root/'cache.parquet'
            rows=[dict(MRN='privateA',ECGDate='2020-01-01',FileID='valid',fileID='other'),
                  dict(MRN='privateA',ECGDate='2020-01-02',FileID='same_day',fileID='same_day'),
                  dict(MRN='privateB',ECGDate='2020-01-01',FileID='collision',fileID='collision'),
                  dict(MRN='outside',ECGDate='2020-01-01',FileID='collision',fileID='collision'),
                  dict(MRN='privateB',ECGDate='2020-01-01',FileID='../unsafe',fileID='duplicated')]
            pq.write_table(pa.Table.from_pylist(rows),metadata)
            pq.write_table(pa.table({'file_id':['valid','other','collision','same_day','duplicated','duplicated']}),cache)
            (vectors/'valid.npy').write_bytes(b'presence only')
            result=audit([dict(patient_key=p,index_date=date(2020,1,2),treatment_arm='arm') for p in ('privateA','privateB')],metadata,{'clmbr':cache},vectors)
            c={(r['metadata_alias'],r['evidence']):r['patients'] for r in result['coverage']}
            self.assertEqual(c['FileID','same_ecg_file_and_clmbr'],1)
            self.assertEqual(c['fileID','clmbr'],1)
            self.assertEqual(result['ambiguous_candidate_file_ids'],1)
            self.assertEqual(result['qc']['cohort_same_day_rows'],1)
            self.assertEqual(result['cache_qc']['clmbr']['duplicate_nonempty_file_ids'],1)
            self.assertNotIn('privateA',str(result)); self.assertNotIn('collision\'',str(result))
    def test_dates_are_conservative(self):
        for value in ['01/02/2020','2020-01-01T00:00:00Z','2020-02-30',None]:
            self.assertIsNone(day(value))
        self.assertEqual(day('2020-01-01 12:34'),date(2020,1,1))
