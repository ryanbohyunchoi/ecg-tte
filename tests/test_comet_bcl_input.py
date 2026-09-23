import sys,tempfile,unittest
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_comet_bcl_input import select,safe_id
class SelectionTests(unittest.TestCase):
    def test_timing_alias_conflict_and_no_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);wave=root/'waves';wave.mkdir()
            for fid in ('old','ok','a','b','collision','same','future'):(wave/(fid+'.npy')).write_bytes(b'synthetic-not-a-waveform')
            rows=[dict(MRN='p1',ECGDate='2020-01-01',FileID='missing1',fileID='old'),dict(MRN='p1',ECGDate='2020-01-09',FileID='missing2',fileID='gone'),dict(MRN='p2',ECGDate='2020-01-09',FileID='missing3',fileID='ok'),dict(MRN='p2',ECGDate='2020-01-10',FileID='same',fileID='same'),dict(MRN='p2',ECGDate='2020-01-11',FileID='future',fileID='future'),dict(MRN='p3',ECGDate='2020-01-09',FileID='a',fileID='b'),dict(MRN='p4',ECGDate='2020-01-09',FileID='collision',fileID='collision'),dict(MRN='outside',ECGDate='2020-01-09',FileID='collision',fileID='collision')]
            meta=root/'meta.parquet';pq.write_table(pa.Table.from_pylist(rows),meta)
            formats=root/'formats.csv';formats.write_text('fileID,format_new\nok,5_0\nold,other\na,other\nb,other\ncollision,other\n')
            roster=[dict(patient_key=p,treatment_arm='synthetic_arm',index_date='2020-01-10') for p in ('p1','p2','p3','p4','p5')]
            result,qc=select(roster,meta,wave,formats)
            self.assertEqual([r['status'] for r in result],['no_latest_day_waveform','selected_for_smoke','multiple_waveform_aliases_unresolved','ambiguous_latest_day_identity','no_prior365_ecg'])
            self.assertEqual(result[1]['fileID'],'ok');self.assertTrue(result[1]['format_250hz']);self.assertEqual(result[1]['lag_days'],1)
            formats.write_text('fileID,format_new\nok,5_0\nok,other\n')
            self.assertEqual(select(roster,meta,wave,formats)[0][1]['status'],'conflicting_sampling_formats')
    def test_path_safety(self):
        for bad in ('../x','x/y','x\\y','x\nq',None):self.assertIsNone(safe_id(bad))
if __name__=='__main__':unittest.main()
